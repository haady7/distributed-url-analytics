# API quick reference

Base URL: `http://localhost:8000`

## Register and login

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"dev@example.com","password":"StrongPass!234"}'

curl -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"dev@example.com","password":"StrongPass!234"}'
```

Copy `access_token` from the login response and set it in your shell:

```bash
export TOKEN='paste-access-token-here'
```

## Create a short URL

```bash
curl -X POST http://localhost:8000/api/v1/urls \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"original_url":"https://fastapi.tiangolo.com/","custom_code":"fastapi-docs"}'
```

To generate a code automatically, omit `custom_code`. For an expiry, add an ISO-8601 timestamp such as `"expires_at":"2027-01-01T00:00:00Z"`.

## Follow and inspect analytics

```bash
curl -i http://localhost:8000/fastapi-docs
curl http://localhost:8000/api/v1/urls/fastapi-docs/analytics \
  -H "Authorization: Bearer $TOKEN"
```

## Deactivate a link

```bash
curl -X DELETE http://localhost:8000/api/v1/urls/fastapi-docs \
  -H "Authorization: Bearer $TOKEN"
```

Interactive API docs: `http://localhost:8000/docs`.
