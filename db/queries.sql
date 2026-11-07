-- 1) Overdue / due-soon checks per aircraft (dashboard alert)
SELECT a.registration, m.check_type, m.next_due, m.status
FROM maintenance_schedule m JOIN aircraft a USING(aircraft_id)
WHERE m.status IN ('Overdue','Due Soon') ORDER BY m.next_due;

-- 2) Parts that need reordering
SELECT name, quantity_in_stock, reorder_level, supplier, lead_time_days
FROM parts_inventory WHERE quantity_in_stock <= reorder_level ORDER BY quantity_in_stock;

-- 3) Open work orders with aircraft, technician and part
SELECT w.work_order_id, a.registration, d.description, d.severity, t.name AS technician, p.name AS part
FROM work_orders w JOIN aircraft a USING(aircraft_id) JOIN defect_reports d USING(defect_id)
JOIN technicians t USING(technician_id) JOIN parts_inventory p USING(part_id)
WHERE w.status IN ('Open','In Progress') ORDER BY w.priority;

-- 4) Defects per ATA system
SELECT system, COUNT(*) AS defects, SUM(severity='Critical') AS critical FROM defect_reports GROUP BY system ORDER BY defects DESC;

-- 5) Real FAA reports about the A320 by system
SELECT ata_system, COUNT(*) AS reports FROM faa_sdr_reports WHERE is_a320=1 AND ata_system IS NOT NULL GROUP BY ata_system ORDER BY reports DESC;

-- 6) Maintenance cost per aircraft
SELECT a.registration, ROUND(SUM(w.labor_cost_usd + w.part_qty*p.unit_cost_usd),0) AS total_cost_usd
FROM work_orders w JOIN aircraft a USING(aircraft_id) JOIN parts_inventory p USING(part_id) GROUP BY a.registration ORDER BY total_cost_usd DESC LIMIT 10;
