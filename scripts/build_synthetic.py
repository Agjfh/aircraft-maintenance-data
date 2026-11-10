"""Build the coherent synthetic A320 maintenance dataset (reproducible, seed=320).

Usage: python scripts/build_synthetic.py      (then: python db/seed.py)

What it does
- Keeps aircraft.csv and engines.csv as they are (already consistent: -214 -> CFM56-5B, -232 -> V2500).
- Writes the reference catalog: symptoms, fault_catalog, fault_symptoms, parts_inventory (with ATA code,
  function, interval and inspection checklist).
- Regenerates defect_reports / defect_symptoms / work_orders so that symptom -> fault -> ATA system -> part
  is consistent (this is what the diagnosis model learns from).
- Adds component_status (per-aircraft last serviced / next due / status) for the app's parts screens.
- Fixes technicians (Part-66 licence category matches specialty) and maintenance_schedule
  (6-Year / 12-Year checks are calendar checks: interval_months, no flight-hour interval).
- Links engine_sensor_data to real engine_id values and rescales sensor columns to plausible
  cruise ranges (trend over cycles is preserved; the step is idempotent).

All reference text (checklists, recommended checks) is generic and illustrative. It is NOT taken from the
Airbus AMM / TSM / MPD and must not be used for real maintenance.
"""
import os, json, numpy as np, pandas as pd

os.chdir(os.path.join(os.path.dirname(__file__), ".."))
R = "data/raw/a320_synthetic/"
TODAY = pd.Timestamp("2026-11-10")
rng = np.random.default_rng(320)

# ----------------------------------------------------------------------------------------------
# 1) Symptoms the technician can tick in the app (source = who usually reports it)
# ----------------------------------------------------------------------------------------------
SYMPTOMS = [
    # id, name, category, typical source
    ("S01", "Hydraulic system low pressure warning", "Cockpit warning", "Pilot"),
    ("S02", "Hydraulic reservoir low level", "Indication", "Line Mechanic"),
    ("S03", "Hydraulic fluid leak / wet area", "Visual", "Line Mechanic"),
    ("S04", "Engine oil pressure low", "Indication", "Pilot"),
    ("S05", "Engine oil quantity decreasing faster than normal", "Trend", "Automated Monitoring"),
    ("S06", "Oil leak / oil streaks on cowling", "Visual", "Line Mechanic"),
    ("S07", "Oil filter clog indication", "Cockpit warning", "Pilot"),
    ("S08", "Engine vibration above limit", "Indication", "Pilot"),
    ("S09", "EGT higher than normal / EGT margin loss", "Trend", "Automated Monitoring"),
    ("S10", "Fuel flow fluctuation", "Indication", "Pilot"),
    ("S11", "Engine thrust / N1 response sluggish", "Pilot report", "Pilot"),
    ("S12", "Visible fan blade damage / FOD", "Visual", "Inspection"),
    ("S13", "Fuel pump low pressure warning", "Cockpit warning", "Pilot"),
    ("S14", "Fuel quantity indication disagree", "Indication", "Pilot"),
    ("S15", "Brake temperature high", "Indication", "Pilot"),
    ("S16", "Brake wear pin at or below limit", "Visual", "Inspection"),
    ("S17", "Tyre cut / tread wear beyond limit", "Visual", "Line Mechanic"),
    ("S18", "Tyre pressure low", "Indication", "Line Mechanic"),
    ("S19", "Landing gear shock strut low extension", "Visual", "Line Mechanic"),
    ("S20", "Landing gear not uplocked / gear disagree", "Cockpit warning", "Pilot"),
    ("S21", "Air data disagree (speed / altitude)", "Cockpit warning", "Pilot"),
    ("S22", "Angle-of-attack disagree", "Cockpit warning", "Pilot"),
    ("S23", "Probe heat fault", "Cockpit warning", "Pilot"),
    ("S24", "Navigation display / IR alignment fault", "Cockpit warning", "Pilot"),
    ("S25", "Weather radar display blank or unreliable", "Pilot report", "Pilot"),
    ("S26", "Pack outlet overheat / cabin too hot", "Cockpit warning", "Cabin Crew"),
    ("S27", "Cabin pressure fluctuation / ear discomfort", "Pilot report", "Cabin Crew"),
    ("S28", "Bleed air overheat / bleed fault", "Cockpit warning", "Pilot"),
    ("S29", "IDG oil overheat / low pressure", "Cockpit warning", "Pilot"),
    ("S30", "Generator or battery fault", "Cockpit warning", "Pilot"),
    ("S31", "Fire detection loop fault", "Cockpit warning", "Pilot"),
    ("S32", "Flap / slat asymmetry or slow movement", "Cockpit warning", "Pilot"),
    ("S33", "Flight control computer fault", "Cockpit warning", "Pilot"),
    ("S34", "APU fails to start", "Pilot report", "Pilot"),
    ("S35", "APU EGT overtemperature / auto shutdown", "Cockpit warning", "Pilot"),
    ("S36", "Door not closed indication", "Cockpit warning", "Cabin Crew"),
    ("S37", "Abnormal noise or vibration in cabin", "Pilot report", "Cabin Crew"),
    ("S38", "Corrosion / paint blistering on structure", "Visual", "Inspection"),
    ("S39", "Dent / impact mark on skin or radome", "Visual", "Inspection"),
    ("S40", "Bird remains / blood on structure", "Visual", "Line Mechanic"),
]

# ----------------------------------------------------------------------------------------------
# 2) Parts catalog (part_id, part_number, name, ATA, system, category, cost, stock, reorder, supplier,
#    lead days, shelf months, function, interval text, interval_fh, interval_months, checklist)
# ----------------------------------------------------------------------------------------------
P = [
 ("P001","PN-21510","Air Cycle Machine","21-51","Air Conditioning","Air Conditioning",42000,2,1,"Liebherr Aerospace",30,None,
  "Cools and expands bleed air in the air-conditioning pack to supply conditioned air to the cabin.","On condition",None,None,
  "Check pack outlet temperature trend|Inspect ACM for oil traces and abnormal noise|Check inlet/outlet ducts and clamps|Verify bearing free rotation"),
 ("P002","PN-21310","Cabin Pressure Controller","21-31","Air Conditioning","Pressurization",16500,2,1,"Liebherr Aerospace",21,None,
  "Controls the outflow valve to keep cabin altitude and rate of change within limits.","On condition",None,None,
  "Read controller BITE / fault history|Check outflow valve operation in manual mode|Inspect static ports and sensing lines|Run pressurization functional test"),
 ("P003","PN-24221","Integrated Drive Generator (IDG)","24-22","Electrical Power","Electrical",95000,1,1,"Collins Aerospace",45,None,
  "Engine-driven generator that supplies constant-frequency AC power.","Oil check every A-Check",750,None,
  "Check IDG oil level sight glass|Inspect oil filter differential pressure indicator|Check for oil leaks at mounting flange|Verify disconnect mechanism condition"),
 ("P004","PN-24380","Main Battery (Ni-Cd)","24-38","Electrical Power","Electrical",6200,4,2,"Saft",14,24,
  "Provides DC power for APU start and emergency electrical supply.","Capacity check every 12 months",None,12,
  "Measure battery voltage on BAT display|Check vent tubes and connector|Inspect for electrolyte leakage|Perform capacity check if due"),
 ("P005","PN-26120","Engine Fire Detection Loop","26-12","Fire Protection","Fire Protection",4800,6,2,"Kidde Aerospace",10,None,
  "Detects fire or overheat in the engine nacelle and triggers the fire warning.","On condition",None,None,
  "Run fire detection system test|Measure loop resistance / continuity|Inspect loop routing and clamps|Check connectors for chafing"),
 ("P006","PN-27510","Flap Drive Actuator","27-51","Flight Controls","Flight Controls",28000,2,1,"Liebherr Aerospace",30,None,
  "Transmits torque from the flap power control unit to move the flap panels.","Lubrication every C-Check",7500,None,
  "Check flap position and asymmetry log|Inspect actuator for leaks and play|Lubricate per task card|Run flap extension/retraction test"),
 ("P007","PN-27930","Elevator Aileron Computer (ELAC)","27-93","Flight Controls","Avionics",68000,1,1,"Thales",25,None,
  "Fly-by-wire computer controlling elevator, aileron and stabilizer.","On condition",None,None,
  "Read CFDS fault history|Reset computer and recheck|Check connector and rack cooling|Replace LRU if fault persists"),
 ("P008","PN-28210","Fuel Tank Booster Pump","28-21","Fuel","Fuel",14500,4,2,"Eaton",14,None,
  "Supplies pressurized fuel from the tank to the engine feed line.","On condition",None,None,
  "Check pump low-pressure indication|Measure pump current|Inspect canister for leaks|Run pump functional test"),
 ("P009","PN-28420","Fuel Quantity Probe","28-42","Fuel","Fuel",3900,8,3,"Safran",10,None,
  "Capacitance probe measuring fuel height in the tank for quantity indication.","On condition",None,None,
  "Compare FQI with dipstick / magnalevel reading|Read FQIC fault history|Check probe harness continuity|Replace faulty probe"),
 ("P010","PN-29110","Engine-Driven Hydraulic Pump (Green)","29-11","Hydraulic Power","Hydraulics",21000,2,2,"Parker Aerospace",7,None,
  "Engine-driven pump that pressurizes the green hydraulic system.","On condition",None,None,
  "Check system pressure on ECAM HYD page|Inspect pump case drain filter|Check for leaks at pump and lines|Verify reservoir level and pressurization"),
 ("P011","PN-29150","Hydraulic Hose & Seal Kit","29-11","Hydraulic Power","Hydraulics",650,30,10,"Parker Aerospace",5,60,
  "Hoses, O-rings and seals used to repair hydraulic leaks.","On condition",None,None,
  "Clean area and locate leak source|Check fitting torque|Replace hose / seal|Leak check under pressure and refill reservoir"),
 ("P012","PN-30310","Pitot Probe","30-31","Ice & Rain Protection","Avionics",5200,6,2,"Collins Aerospace",10,None,
  "Measures total pressure for airspeed; heated to prevent icing.","Inspection every A-Check",750,None,
  "Inspect probe for damage and blockage|Check probe heater current|Check drain holes|Run air data test after replacement"),
 ("P013","PN-32420","Main Wheel Brake Assembly","32-42","Landing Gear","Landing Gear",35000,6,3,"Safran Landing Systems",14,None,
  "Carbon multi-disc brake that decelerates the main wheels.","Wear pin check daily",None,None,
  "Measure brake wear pin length|Check brake temperature history|Inspect for hydraulic leaks at piston housing|Replace brake if pin at limit"),
 ("P014","PN-32410","Main Wheel Tyre (46x16R20)","32-41","Landing Gear","Landing Gear",4500,20,8,"Michelin",7,60,
  "Main landing gear tyre.","Pressure check daily",None,None,
  "Check tyre pressure cold|Inspect tread depth and cuts|Check for bulges and sidewall damage|Replace and record if beyond limits"),
 ("P015","PN-32110","MLG Shock Absorber Seal Kit","32-11","Landing Gear","Landing Gear",2800,6,2,"Safran Landing Systems",14,48,
  "Seals for the main landing gear shock absorber.","Servicing check every A-Check",750,None,
  "Measure shock strut extension|Check for fluid leaks at chrome|Service nitrogen / oil per chart|Replace seals if leaking"),
 ("P016","PN-32310","Landing Gear Proximity Sensor","32-31","Landing Gear","Landing Gear",2100,8,3,"Crane Aerospace",10,None,
  "Detects gear up/down-lock and door positions for the LGCIU.","On condition",None,None,
  "Read LGCIU fault history|Measure sensor target gap|Check harness and connector|Run gear retraction test on jacks"),
 ("P017","PN-34110","Angle-of-Attack Sensor","34-11","Navigation","Avionics",24000,3,1,"Thales",21,None,
  "Measures the aircraft angle of attack for flight controls and protections.","On condition",None,None,
  "Inspect vane for damage and free movement|Check heater operation|Read ADIRU fault history|Run AOA test after replacement"),
 ("P018","PN-34120","ADIRU","34-12","Navigation","Avionics",120000,1,1,"Northrop Grumman",30,None,
  "Air data and inertial reference unit supplying attitude, heading, speed and altitude.","On condition",None,None,
  "Read BITE / CFDS fault history|Check alignment and IR status|Inspect connector and rack|Replace LRU and run alignment"),
 ("P019","PN-34410","Weather Radar Transceiver","34-41","Navigation","Avionics",55000,1,1,"Collins Aerospace",30,None,
  "Transmits and receives radar signals to display weather ahead of the aircraft.","On condition",None,None,
  "Run radar self-test|Inspect radome and waveguide|Check antenna drive|Replace transceiver if test fails"),
 ("P020","PN-36110","Bleed Pressure Regulating Valve","36-11","Pneumatic","Pneumatic",18000,2,1,"Honeywell",21,None,
  "Regulates engine bleed air pressure supplied to the pneumatic system.","On condition",None,None,
  "Check bleed pressure and temperature on ECAM|Inspect valve and sense lines|Check precooler for blockage|Run bleed system test"),
 ("P021","PN-49410","APU Starter Motor","49-41","APU","APU",12000,2,1,"Honeywell",21,None,
  "Electric motor that cranks the APU during start.","On condition",None,None,
  "Check battery voltage before start|Inspect starter brushes / connector|Check start sequence on ECB|Replace starter if no rotation"),
 ("P022","PN-49310","APU Fuel Control Unit","49-31","APU","APU",26000,1,1,"Honeywell",28,None,
  "Meters fuel to the APU during start and operation.","On condition",None,None,
  "Read APU ECB fault history|Check fuel supply pressure|Inspect EGT thermocouples|Replace FCU if overtemp repeats"),
 ("P023","PN-52710","Door Proximity Sensor","52-71","Doors","Cabin Safety",1500,10,4,"Crane Aerospace",7,None,
  "Detects door closed / locked status for the door warning system.","On condition",None,None,
  "Check door indication on ECAM DOOR page|Measure sensor target gap|Inspect harness|Adjust or replace sensor"),
 ("P024","PN-53100","Corrosion Inhibitor & Repair Kit","53-00","Fuselage","Airframe",450,40,15,"AkzoNobel Aerospace",5,24,
  "Materials for removing corrosion and restoring protective treatment.","Per structural inspection program",None,None,
  "Remove paint and assess corrosion depth|Blend out within limits|Apply surface treatment and primer|Record and report if beyond limits"),
 ("P025","PN-53150","Nose Radome","53-15","Fuselage","Airframe",38000,1,1,"Saint-Gobain",45,None,
  "Composite nose cover protecting the weather radar antenna.","Inspection every A-Check",750,None,
  "Inspect for impact, cracks and delamination|Tap test damaged area|Check lightning strips|Repair or replace"),
 ("P026","PN-72210","Fan Blade (CFM56-5B)","72-21","Engine","Engine",15500,6,2,"CFM International",30,None,
  "Fan blade that produces most of the engine thrust.","Borescope / visual every A-Check",750,None,
  "Inspect blades for nicks, dents and cracks|Check blend limits|Check fan rotation for rubbing|Replace / blend and balance"),
 ("P027","PN-72510","HPT Blade Set (CFM56-5B)","72-51","Engine","Engine",185000,1,1,"CFM International",60,None,
  "High-pressure turbine blades driving the high-pressure compressor.","Borescope on EGT trend",None,None,
  "Review EGT margin trend|Borescope HPT stage 1 blades|Check for burn and coating loss|Plan engine shop visit if beyond limits"),
 ("P028","PN-73210","Fuel Metering Unit (FMU)","73-21","Engine Fuel & Control","Engine",48000,1,1,"Safran",30,None,
  "Meters fuel flow to the combustor as commanded by the FADEC.","On condition",None,None,
  "Read FADEC fault history|Check fuel flow transmitter|Inspect FMU connectors|Replace FMU and run engine test"),
 ("P029","PN-79310","Oil Pressure Transmitter","79-31","Oil","Engine",3200,4,2,"Honeywell",14,None,
  "Measures engine oil pressure for cockpit indication.","On condition",None,None,
  "Compare indication with direct gauge|Check transmitter connector|Inspect sense line for leaks|Replace transmitter"),
 ("P030","PN-79210","Engine Oil Filter Element","79-21","Oil","Consumables",280,40,15,"Pall Aerospace",5,60,
  "Removes contaminants from the engine lubrication oil.","Replace every C-Check or on clog",7500,None,
  "Check clog indicator|Remove filter and inspect debris|Send debris for analysis if found|Install new element and leak check"),
 ("P031","PN-79010","Engine Oil Seal Kit","79-00","Oil","Engine",950,20,6,"CFM International",7,60,
  "Seals and gaskets for oil system leak repair.","On condition",None,None,
  "Clean area and locate leak|Check oil consumption trend|Replace seal / gasket|Ground run and leak check"),
]
parts = pd.DataFrame(P, columns=["part_id","part_number","name","ata_code","system","category","unit_cost_usd",
    "quantity_in_stock","reorder_level","supplier","lead_time_days","shelf_life_months","function",
    "maintenance_interval","interval_flight_hours","interval_months","inspection_checklist"])

# ----------------------------------------------------------------------------------------------
# 3) Fault catalog: fault -> ATA, part, default severity, symptom probabilities, recommended checks
# ----------------------------------------------------------------------------------------------
F = [
 ("F01","Pack outlet overheat (air cycle machine degradation)","21-51","P001","Major",{"S26":.95,"S37":.3,"S28":.2},
  "Check pack outlet temperature|Inspect ACM and heat exchanger|Clean heat exchanger if blocked"),
 ("F02","Cabin pressure controller fault","21-31","P002","Major",{"S27":.95,"S37":.25},
  "Read controller fault history|Test outflow valve|Check static sensing lines"),
 ("F03","IDG oil overheat / low oil","24-22","P003","Major",{"S29":.95,"S30":.35,"S06":.2},
  "Check IDG oil level|Inspect filter indicator|Look for oil leaks at IDG"),
 ("F04","Main battery fault","24-38","P004","Major",{"S30":.95,"S34":.4},
  "Measure battery voltage|Check connector and vent|Capacity check or replace battery"),
 ("F05","Engine fire detection loop fault","26-12","P005","Major",{"S31":.97},
  "Run fire test|Check loop resistance|Inspect routing for chafing"),
 ("F06","Flap drive actuator wear","27-51","P006","Major",{"S32":.95,"S37":.25,"S03":.2},
  "Check asymmetry log|Inspect actuator for leaks and play|Run flap test"),
 ("F07","ELAC computer fault","27-93","P007","Critical",{"S33":.97,"S22":.15},
  "Read CFDS history|Reset and retest|Replace ELAC if fault persists"),
 ("F08","Fuel tank booster pump failure","28-21","P008","Major",{"S13":.95,"S10":.3},
  "Check pump low-pressure warning|Measure pump current|Replace pump"),
 ("F09","Fuel quantity indication fault","28-42","P009","Minor",{"S14":.95},
  "Compare FQI with manual reading|Read FQIC history|Check probe harness"),
 ("F10","Green engine-driven hydraulic pump failure","29-11","P010","Critical",{"S01":.95,"S02":.4,"S03":.25},
  "Check HYD page pressure|Inspect case drain filter|Replace EDP"),
 ("F11","Hydraulic line or seal leak","29-11","P011","Major",{"S03":.95,"S02":.75,"S01":.3},
  "Locate leak source|Replace hose / seal|Leak check and refill"),
 ("F12","Pitot probe heater failure","30-31","P012","Major",{"S23":.95,"S21":.5},
  "Check probe heater current|Inspect probe|Run air data test"),
 ("F13","Brake wear beyond limit","32-42","P013","Minor",{"S16":.97,"S15":.35},
  "Measure wear pin|Check brake temperature history|Replace brake"),
 ("F14","Tyre damage / wear beyond limit","32-41","P014","Minor",{"S17":.95,"S18":.4},
  "Check pressure and tread|Inspect for cuts and bulges|Replace tyre"),
 ("F15","MLG shock absorber leak / under-serviced","32-11","P015","Major",{"S19":.95,"S03":.35},
  "Measure strut extension|Check for leaks|Service or replace seals"),
 ("F16","Landing gear proximity sensor fault","32-31","P016","Critical",{"S20":.95},
  "Read LGCIU history|Check sensor gap|Gear retraction test on jacks"),
 ("F17","Angle-of-attack sensor fault","34-11","P017","Critical",{"S22":.95,"S21":.4},
  "Inspect AOA vane|Check heater|Replace sensor and test"),
 ("F18","ADIRU fault","34-12","P018","Critical",{"S24":.95,"S21":.5},
  "Read BITE history|Check alignment|Replace ADIRU"),
 ("F19","Weather radar transceiver fault","34-41","P019","Minor",{"S25":.97},
  "Run radar self-test|Inspect radome / waveguide|Replace transceiver"),
 ("F20","Bleed pressure regulating valve fault","36-11","P020","Major",{"S28":.95,"S26":.3},
  "Check bleed indications|Inspect valve and sense lines|Run bleed test"),
 ("F21","APU starter failure","49-41","P021","Minor",{"S34":.95,"S30":.2},
  "Check battery voltage|Inspect starter|Replace starter"),
 ("F22","APU fuel control / overtemperature","49-31","P022","Major",{"S35":.95,"S34":.3},
  "Read ECB history|Check fuel supply|Inspect EGT thermocouples"),
 ("F23","Door proximity sensor fault","52-71","P023","Minor",{"S36":.97},
  "Check DOOR page|Adjust sensor gap|Replace sensor"),
 ("F24","Fuselage corrosion","53-00","P024","Minor",{"S38":.97},
  "Assess corrosion depth|Blend out within limits|Apply treatment and report"),
 ("F25","Bird strike damage (radome / structure)","53-15","P025","Major",{"S40":.9,"S39":.75,"S25":.2,"S08":.15},
  "Inspect impact area|Check radome and probes|Engine inspection if ingested"),
 ("F26","Fan blade FOD damage","72-21","P026","Critical",{"S12":.9,"S08":.75,"S40":.25},
  "Inspect fan blades|Check blend limits|Engine vibration survey"),
 ("F27","HPT blade deterioration (EGT margin loss)","72-51","P027","Major",{"S09":.95,"S11":.35,"S10":.15},
  "Review EGT trend|Borescope HPT|Plan shop visit"),
 ("F28","Fuel metering unit fault","73-21","P028","Major",{"S10":.95,"S11":.5},
  "Read FADEC history|Check fuel flow transmitter|Replace FMU"),
 ("F29","Engine oil pressure indication fault","79-31","P029","Minor",{"S04":.95},
  "Compare with direct gauge|Check transmitter connector|Replace transmitter"),
 ("F30","Engine oil filter clogging","79-21","P030","Major",{"S07":.95,"S04":.35},
  "Check clog indicator|Inspect filter debris|Replace filter"),
 ("F31","Engine oil leak","79-00","P031","Major",{"S06":.95,"S05":.75,"S04":.2},
  "Locate leak|Check consumption trend|Replace seal and leak check"),
]
pmap = parts.set_index("part_id")
faults = pd.DataFrame([{
    "fault_id": f, "fault_name": n, "ata_code": a, "ata_chapter": a[:2], "system": pmap.loc[p, "system"],
    "likely_part_id": p, "default_severity": s, "recommended_checks": rc} for f, n, a, p, s, _, rc in F])
fault_symptoms = pd.DataFrame([{"fault_id": f, "symptom_id": sid, "probability": pr}
                               for f, _, _, _, _, sy, _ in F for sid, pr in sy.items()])
symptoms = pd.DataFrame(SYMPTOMS, columns=["symptom_id", "name", "category", "typical_source"])
assert fault_symptoms.symptom_id.isin(symptoms.symptom_id).all()

# relative frequency of faults in the fleet (common line findings more frequent)
freq = {"F13": 6, "F14": 6, "F24": 4, "F31": 4, "F11": 4, "F09": 3, "F23": 3, "F29": 3, "F19": 2, "F21": 2,
        "F25": 2, "F26": 1, "F07": 1, "F16": 1, "F18": 1, "F17": 1, "F10": 1.5}
w = np.array([freq.get(f, 2) for f in faults.fault_id], float); w /= w.sum()

# ----------------------------------------------------------------------------------------------
# 4) Defect reports + symptoms observed + work orders (coherent)
# ----------------------------------------------------------------------------------------------
aircraft = pd.read_csv(R + "aircraft.csv")
tech = pd.read_csv(R + "technicians.csv")
# Part-66: B1 = mechanical (structures, engines, systems), B2 = avionics/electrical, A = line tasks
tech.loc[tech.specialty.isin(["Avionics", "Electrical"]), "license_category"] = "B2 (Avionics)"
tech.loc[(tech.license_category == "B2 (Avionics)") & ~tech.specialty.isin(["Avionics", "Electrical"]),
         "license_category"] = "B1.1 (Mechanical)"
tech_by_spec = {
    "Avionics": ["Navigation", "Flight Controls", "Ice & Rain Protection", "Fire Protection", "Doors"],
    "Electrical": ["Electrical Power", "Fire Protection", "Doors"],
    "Engines": ["Engine", "Engine Fuel & Control", "Oil", "APU", "Pneumatic", "Fuel"],
    "Landing Gear": ["Landing Gear"],
    "Hydraulics": ["Hydraulic Power", "Flight Controls", "Landing Gear"],
    "Airframe/Structures": ["Fuselage", "Doors", "Air Conditioning", "Fuel"],
}
def pick_tech(system):
    ok = tech[tech.specialty.map(lambda s: system in tech_by_spec.get(s, []))]
    return (ok if len(ok) else tech).sample(1, random_state=int(rng.integers(1e9))).technician_id.iloc[0]

N = 1200
start, end = pd.Timestamp("2025-05-18"), pd.Timestamp("2026-11-07")
sym_name = symptoms.set_index("symptom_id")
sev_order = ["Minor", "Major", "Critical"]
D, DS, WO = [], [], []
fault_ids = faults.fault_id.to_numpy()
for i in range(N):
    fr = faults.iloc[rng.choice(len(faults), p=w)]
    fs = fault_symptoms[fault_symptoms.fault_id == fr.fault_id]
    seen = [r.symptom_id for r in fs.itertuples() if rng.random() < r.probability]
    if not seen:
        seen = [fs.sort_values("probability").symptom_id.iloc[-1]]
    if rng.random() < 0.15:                                   # unrelated noise symptom
        seen.append(symptoms.symptom_id.iloc[rng.integers(len(symptoms))])
    seen = list(dict.fromkeys(seen))
    k = sev_order.index(fr.default_severity) + rng.choice([-1, 0, 0, 0, 0, 1])
    sev = sev_order[int(np.clip(k, 0, 2))]
    date = start + pd.Timedelta(days=int(rng.integers((end - start).days + 1)))
    did = f"D{i+1:04d}"
    main = fs.sort_values("probability").symptom_id.iloc[-1]
    reporter = sym_name.loc[seen[0] if seen[0] in fs.symptom_id.values else main, "typical_source"]
    ac = aircraft.aircraft_id.iloc[rng.integers(len(aircraft))]
    D.append({"defect_id": did, "aircraft_id": ac, "reported_date": date.date(), "ata_chapter": fr.ata_chapter,
              "system": fr.system, "description": sym_name.loc[seen[0], "name"][:120], "severity": sev,
              "reported_by": reporter, "aircraft_grounded": int(sev == "Critical" and rng.random() < 0.6),
              "fault_id": fr.fault_id})
    DS += [{"defect_id": did, "symptom_id": s} for s in seen]
    # work order
    age = (TODAY - date).days
    status = ("Closed" if age > 21 or rng.random() < 0.6 else rng.choice(["Open", "In Progress"])) \
        if not (sev == "Minor" and rng.random() < 0.08) else "Deferred"
    labor = round(float(rng.gamma(2.2, 3.0)) + (6 if sev == "Critical" else 0), 1)
    close = (date + pd.Timedelta(days=int(rng.integers(0, 8 if sev != "Minor" else 15)))).date() if status == "Closed" else None
    WO.append({"work_order_id": f"WO{i+1:05d}", "defect_id": did, "aircraft_id": ac, "type": "Corrective",
               "priority": {"Critical": "High", "Major": "Medium", "Minor": "Low"}[sev], "status": status,
               "technician_id": pick_tech(fr.system), "part_id": fr.likely_part_id,
               "part_qty": int(rng.integers(1, 3)) if pmap.loc[fr.likely_part_id, "category"] == "Consumables" else 1,
               "labor_hours": labor, "labor_cost_usd": round(labor * 55, 2), "opened_date": date.date(),
               "closed_date": close})
defects, defect_symptoms, work_orders = pd.DataFrame(D), pd.DataFrame(DS), pd.DataFrame(WO)
work_orders["closed_date"] = pd.to_datetime(work_orders.closed_date).clip(upper=TODAY).dt.date

# keep aircraft status coherent with open critical grounding defects
open_wo = work_orders[work_orders.status.isin(["Open", "In Progress"])].merge(defects, on=["defect_id", "aircraft_id"])
aog = set(open_wo[open_wo.aircraft_grounded == 1].aircraft_id)
in_mx = set(open_wo.aircraft_id) - aog
aircraft["status"] = aircraft.aircraft_id.map(lambda a: "Grounded (AOG)" if a in aog else
                                              ("In Maintenance" if a in in_mx and rng.random() < 0.3 else "Active"))

# ----------------------------------------------------------------------------------------------
# 5) Component status per aircraft (feeds the app's parts list: last serviced / next due / status)
# ----------------------------------------------------------------------------------------------
def status_for(next_due):
    days = (next_due - TODAY).days
    return "Overdue" if days < 0 else ("Due Soon" if days <= 30 else "OK")
CS = []
wo_dates = pd.to_datetime(work_orders.closed_date)
open_by = (work_orders[work_orders.status.isin(["Open", "In Progress", "Deferred"])]
           .groupby(["aircraft_id", "part_id"]).work_order_id.first().to_dict())
for ac in aircraft.itertuples():
    fh_per_day = ac.total_flight_hours / max(1, (TODAY.year - ac.manufacture_year) * 365)
    for p in parts.itertuples():
        done = wo_dates[(work_orders.aircraft_id == ac.aircraft_id) & (work_orders.part_id == p.part_id)].max()
        if pd.isna(p.interval_flight_hours) and pd.isna(p.interval_months):
            # on-condition part: no scheduled due date; last serviced = last closed work order (if any)
            last, nxt, st = (done.date() if pd.notna(done) else None), None, "OK"
        else:
            span = int(p.interval_months * 30.4) if pd.notna(p.interval_months) else int(p.interval_flight_hours / fh_per_day)
            last_ts = TODAY - pd.Timedelta(days=int(rng.integers(0, int(span * 1.08) + 1)))
            if pd.notna(done) and done > last_ts:
                last_ts = done
            nxt_ts = last_ts + pd.Timedelta(days=span)
            last, nxt, st = last_ts.date(), nxt_ts.date(), status_for(nxt_ts)
        CS.append({"aircraft_id": ac.aircraft_id, "part_id": p.part_id, "last_serviced": last, "next_due": nxt,
                   "status": st, "open_work_order_id": open_by.get((ac.aircraft_id, p.part_id))})
component_status = pd.DataFrame(CS)

# ----------------------------------------------------------------------------------------------
# 6) Maintenance schedule: calendar checks get interval_months instead of flight hours
# ----------------------------------------------------------------------------------------------
ms = pd.read_csv(R + "maintenance_schedule.csv")
months = {"A-Check": None, "C-Check": 24, "6-Year Check": 72, "12-Year Check": 144}
ms["interval_months"] = ms.check_type.map(months)
ms.loc[ms.check_type.isin(["6-Year Check", "12-Year Check"]), "interval_flight_hours"] = None
cal = ms.check_type.isin(["6-Year Check", "12-Year Check"])
# keep the planned next_due, derive last_done = next_due - interval (idempotent)
ms.loc[cal, "last_done"] = [str((pd.Timestamp(n) - pd.DateOffset(months=int(m))).date())
                            for n, m in zip(ms.loc[cal, "next_due"], ms.loc[cal, "interval_months"])]
ms["status"] = pd.to_datetime(ms.next_due).map(status_for)
ms = ms[["schedule_id", "aircraft_id", "check_type", "interval_flight_hours", "interval_months",
         "est_duration_hours", "last_done", "next_due", "status"]]
ms["interval_flight_hours"] = ms.interval_flight_hours.astype("Int64")
ms["interval_months"] = ms.interval_months.astype("Int64")

# ----------------------------------------------------------------------------------------------
# 7) Engine sensor data: real engine ids + plausible cruise ranges (min-max rescale, idempotent)
# ----------------------------------------------------------------------------------------------
eng = pd.read_csv(R + "engines.csv")
sd = pd.read_csv(R + "engine_sensor_data.csv")
old_ids = sorted(sd.engine_id.unique())
if not set(old_ids) <= set(eng.engine_id):
    cfm = eng[eng.engine_model.str.startswith("CFM56")].engine_id.tolist()[: len(old_ids)]
    sd["engine_id"] = sd.engine_id.map(dict(zip(old_ids, cfm)))
RANGES = {"egt_c": (620, 760), "compressor_outlet_temp_c": (520, 600), "fan_speed_rpm": (4250, 4400),
          "core_speed_rpm": (13300, 13900), "static_pressure_psi": (44, 48), "oil_pressure_psi": (38, 60),
          "vibration_ips": (0.12, 0.62), "fuel_flow_pph": (2300, 2750)}
for c, (lo, hi) in RANGES.items():
    v = sd[c]; sd[c] = (lo + (v - v.min()) / (v.max() - v.min()) * (hi - lo)).round(2 if c != "vibration_ips" else 4)

# ----------------------------------------------------------------------------------------------
# write
# ----------------------------------------------------------------------------------------------
out = {"symptoms": symptoms, "fault_catalog": faults, "fault_symptoms": fault_symptoms, "parts_inventory": parts,
       "defect_reports": defects, "defect_symptoms": defect_symptoms, "work_orders": work_orders,
       "component_status": component_status, "maintenance_schedule": ms, "technicians": tech,
       "aircraft": aircraft, "engine_sensor_data": sd}
for name, df in out.items():
    df.to_csv(R + f"{name}.csv", index=False)
    print(f"{name:22s} {len(df):6d} rows")

# processed diagnosis dataset: one-hot symptoms -> fault (stratified 70/15/15)
X = pd.crosstab(defect_symptoms.defect_id, defect_symptoms.symptom_id).reindex(columns=symptoms.symptom_id, fill_value=0)
ds = defects[["defect_id", "fault_id", "ata_chapter"]].set_index("defect_id").join(X).reset_index()
from sklearn.model_selection import train_test_split
tr, rest = train_test_split(ds, test_size=0.3, stratify=ds.fault_id, random_state=320)
va, te = train_test_split(rest, test_size=0.5, stratify=rest.fault_id, random_state=320)
os.makedirs("data/processed/diagnosis", exist_ok=True)
for n, d in (("train", tr), ("val", va), ("test", te)):
    d.to_csv(f"data/processed/diagnosis/diagnosis_{n}.csv", index=False)
print("diagnosis splits:", len(tr), len(va), len(te))
