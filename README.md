## Review360 DRF + Postgres (Dockerized)

JWT login endpoints:
- `POST /api/auth/login/` with `{ "email": "...", "password": "..." }`
- `POST /api/token/refresh/` with `{ "refresh": "..." }`

### Run (Docker)
1. Build and start services:
   ```bash
   docker compose up --build -d
   ```
2. Apply migrations and create a superuser:
   ```bash
   docker compose exec web python manage.py migrate
   docker compose exec web python manage.py createsuperuser
   ```
### Registration
- `POST /api/auth/register/` with JSON:
  ```json
  {"email":"user@example.com","password":"<min 8 chars>","first_name":"","last_name":""}
  ```

3. Access: `http://localhost:8000/`

### Environment variables
- `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`
- `CORS_ALLOW_ALL`, `JWT_ACCESS_MIN`, `JWT_REFRESH_DAYS`


