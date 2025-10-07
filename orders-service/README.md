# Orders Service (Windows PowerShell)
## Uso
Set-ExecutionPolicy -Scope Process Bypass -Force
.\bootstrap_orders_service.ps1 -ProjectName orders-service
cd orders-service
docker compose up --build -d
docker compose exec api python run_once_create_db.py
Invoke-RestMethod -Method Post http://localhost:8000/orders 
  -Headers @{"Content-Type"="application/json"; "Idempotency-Key"="abc-123"} 
  -Body '{"customer_id":"c-1","items":[{"sku":"A1","qty":2}]}'
