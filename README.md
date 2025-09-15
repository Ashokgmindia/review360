## Review360 DRF + Postgres (Dockerized)

JWT login endpoints:
- `POST /api/v1/iam/auth/login/` with `{ "email": "...", "password": "..." }`
- `POST /api/v1/iam/token/refresh/` with `{ "refresh": "..." }`

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
### User provisioning (admin-only)
1) Create a superuser:
```bash
docker compose exec web python manage.py createsuperuser
```
2) Authenticate as superuser, then create users via:
- `POST /api/auth/register/` (admin-only) with JSON:
  ```json
  {"email":"user@example.com","password":"<min 8 chars>","first_name":"","last_name":""}
  ```
  Include bearer token from superuser login in the `Authorization: Bearer <access>` header.

3. Access: `http://localhost:8000/`

### Environment variables
- `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`
- `CORS_ALLOWED_ORIGINS` (comma-separated), `JWT_ACCESS_MIN`, `JWT_REFRESH_DAYS`
- DRF throttling: `DRF_THROTTLE_USER`, `DRF_THROTTLE_ANON`, `DRF_THROTTLE_LOGIN`


