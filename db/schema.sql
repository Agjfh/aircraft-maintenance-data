PRAGMA foreign_keys = ON;
CREATE TABLE aircraft(aircraft_id VARCHAR(10) PRIMARY KEY, registration VARCHAR(10) UNIQUE NOT NULL, model VARCHAR(40) NOT NULL, airline VARCHAR(40),
  apu_model VARCHAR(30), manufacture_year INTEGER, seats INTEGER, total_flight_hours INTEGER, total_cycles INTEGER,
  status VARCHAR(20) CHECK(status IN ('Active','In Maintenance','Grounded (AOG)')), base_airport VARCHAR(5));
CREATE TABLE engines(engine_id VARCHAR(20) PRIMARY KEY, aircraft_id VARCHAR(10) NOT NULL REFERENCES aircraft(aircraft_id), position INTEGER CHECK(position IN (1,2)),
  engine_model VARCHAR(30), serial_number VARCHAR(20), hours_since_overhaul INTEGER, cycles_since_overhaul INTEGER, health_index NUMERIC(4,3));
CREATE TABLE technicians(technician_id VARCHAR(10) PRIMARY KEY, name VARCHAR(60) NOT NULL, license_category VARCHAR(30), specialty VARCHAR(40), experience_years INTEGER, shift VARCHAR(10));
CREATE TABLE parts_inventory(part_id VARCHAR(10) PRIMARY KEY, part_number VARCHAR(20), name VARCHAR(80) NOT NULL, category VARCHAR(30), unit_cost_usd NUMERIC(12,2),
  quantity_in_stock INTEGER, reorder_level INTEGER, supplier VARCHAR(40), lead_time_days INTEGER, shelf_life_months INTEGER);
CREATE TABLE maintenance_schedule(schedule_id VARCHAR(10) PRIMARY KEY, aircraft_id VARCHAR(10) NOT NULL REFERENCES aircraft(aircraft_id), check_type VARCHAR(20),
  interval_flight_hours INTEGER, est_duration_hours INTEGER, last_done DATE, next_due DATE, status VARCHAR(10) CHECK(status IN ('OK','Due Soon','Overdue')));
CREATE TABLE defect_reports(defect_id VARCHAR(10) PRIMARY KEY, aircraft_id VARCHAR(10) NOT NULL REFERENCES aircraft(aircraft_id), reported_date DATE, ata_chapter VARCHAR(4),
  system VARCHAR(40), description VARCHAR(120), severity VARCHAR(10) CHECK(severity IN ('Minor','Major','Critical')), reported_by VARCHAR(30), aircraft_grounded INTEGER CHECK(aircraft_grounded IN (0,1)));
CREATE TABLE work_orders(work_order_id VARCHAR(10) PRIMARY KEY, defect_id VARCHAR(10) REFERENCES defect_reports(defect_id), aircraft_id VARCHAR(10) NOT NULL REFERENCES aircraft(aircraft_id),
  type VARCHAR(15), priority VARCHAR(10), status VARCHAR(15) CHECK(status IN ('Open','In Progress','Closed','Deferred')), technician_id VARCHAR(10) REFERENCES technicians(technician_id),
  part_id VARCHAR(10) REFERENCES parts_inventory(part_id), part_qty INTEGER, labor_hours NUMERIC(6,1), labor_cost_usd NUMERIC(10,2), opened_date DATE, closed_date DATE);
CREATE TABLE engine_sensor_data(engine_id VARCHAR(20), cycle INTEGER, egt_c NUMERIC, compressor_outlet_temp_c NUMERIC, fan_speed_rpm NUMERIC, core_speed_rpm NUMERIC,
  static_pressure_psi NUMERIC, oil_pressure_psi NUMERIC, vibration_ips NUMERIC, fuel_flow_pph NUMERIC, rul_cycles INTEGER, PRIMARY KEY(engine_id,cycle));
CREATE TABLE faa_sdr_reports(sdr_id INTEGER PRIMARY KEY, source_id INTEGER, hazard_category VARCHAR(40), is_hazard VARCHAR(20), report_text TEXT,
  part_name VARCHAR(80), part_condition VARCHAR(40), nature_of_condition VARCHAR(80), is_a320 INTEGER, ata_chapter VARCHAR(4), ata_system VARCHAR(40));
CREATE INDEX idx_wo_aircraft ON work_orders(aircraft_id); CREATE INDEX idx_wo_status ON work_orders(status);
CREATE INDEX idx_def_aircraft ON defect_reports(aircraft_id); CREATE INDEX idx_sched_due ON maintenance_schedule(next_due);
CREATE INDEX idx_sdr_a320 ON faa_sdr_reports(is_a320); CREATE INDEX idx_sdr_cat ON faa_sdr_reports(hazard_category);
