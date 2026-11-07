from locust import HttpUser, between, task


class LinkPulseUser(HttpUser):
    wait_time = between(0.2, 1.0)

    @task(8)
    def health_check(self):
        self.client.get("/health/live", name="GET /health/live")

    @task(2)
    def api_docs(self):
        self.client.get("/openapi.json", name="GET /openapi.json")
