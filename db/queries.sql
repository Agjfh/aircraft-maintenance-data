-- 1) Overdue / due-soon checks per aircraft (dashboard alert)
SELECT a.registration, m.check_type, m.next_due, m.status
FROM maintenance_schedule m JOIN aircraft a USING(aircraft_id)
WHERE m.status IN ('Overdue','Due Soon') ORDER BY m.next_due;

-- 2) Dashboard counters for one aircraft (in-service / due-soon / overdue components)
SELECT status, COUNT(*) AS components FROM component_status WHERE aircraft_id = 'AC001' GROUP BY status;

-- 3) Systems screen: parts of one aircraft with ATA code and status
SELECT p.ata_code, p.name, p.system, c.last_serviced, c.next_due, c.status, c.open_work_order_id
FROM component_status c JOIN parts_inventory p USING(part_id)
WHERE c.aircraft_id = 'AC001' ORDER BY p.ata_code;

-- 4) Part Detail screen: function, interval and checklist ('|' separated steps)
SELECT ata_code, name, function, maintenance_interval, inspection_checklist FROM parts_inventory WHERE part_id = 'P013';

-- 5) Diagnose screen: symptom list, and faults linked to the ticked symptoms (simple rule-based ranking,
--    the ML ranking is in ml/diagnosis_model.json)
SELECT symptom_id, name, category FROM symptoms ORDER BY symptom_id;
SELECT f.fault_id, f.fault_name, f.ata_code, ROUND(SUM(fs.probability),2) AS score, f.recommended_checks
FROM fault_symptoms fs JOIN fault_catalog f USING(fault_id)
WHERE fs.symptom_id IN ('S02','S03') GROUP BY f.fault_id ORDER BY score DESC LIMIT 3;

-- 6) Parts that need reordering
SELECT name, quantity_in_stock, reorder_level, supplier, lead_time_days
FROM parts_inventory WHERE quantity_in_stock <= reorder_level ORDER BY quantity_in_stock;

-- 7) Open work orders with aircraft, fault, technician and part
SELECT w.work_order_id, a.registration, f.fault_name, d.severity, t.name AS technician, p.name AS part
FROM work_orders w JOIN aircraft a USING(aircraft_id) JOIN defect_reports d USING(defect_id) JOIN fault_catalog f USING(fault_id)
JOIN technicians t USING(technician_id) JOIN parts_inventory p ON p.part_id = w.part_id
WHERE w.status IN ('Open','In Progress') ORDER BY w.priority;

-- 8) Defects per ATA system (which systems fail most)
SELECT ata_chapter, system, COUNT(*) AS defects, SUM(severity='Critical') AS critical FROM defect_reports GROUP BY system ORDER BY defects DESC;

-- 9) Real FAA reports about the A320 by system
SELECT ata_system, COUNT(*) AS reports FROM faa_sdr_reports WHERE is_a320=1 AND ata_system IS NOT NULL GROUP BY ata_system ORDER BY reports DESC;

-- 10) Maintenance cost per aircraft
SELECT a.registration, ROUND(SUM(w.labor_cost_usd + w.part_qty*p.unit_cost_usd),0) AS total_cost_usd
FROM work_orders w JOIN aircraft a USING(aircraft_id) JOIN parts_inventory p USING(part_id) GROUP BY a.registration ORDER BY total_cost_usd DESC LIMIT 10;

-- 11) Latest engine sensor readings per engine (engine health)
SELECT e.engine_id, a.registration, e.position, s.cycle, s.egt_c, s.vibration_ips, s.rul_cycles
FROM engine_sensor_data s JOIN engines e USING(engine_id) JOIN aircraft a USING(aircraft_id)
WHERE s.cycle = (SELECT MAX(cycle) FROM engine_sensor_data x WHERE x.engine_id = s.engine_id) ORDER BY s.rul_cycles LIMIT 10;
