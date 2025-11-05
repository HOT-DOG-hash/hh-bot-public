# Observability Alerts

Example Prometheus-style rules that cover the new payment metrics:

```yaml
groups:
  - name: payments
    rules:
      - alert: PaymentsFailureRateHigh
        expr: (increase(payments_failed_total[10m]) / clamp_min(increase(payments_initiated_total[10m]), 1)) > 0.08
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Payment failure rate is above 8% (10m window)"
          description: "Investigate YooMoney or quota issues — failures exceeded 8% in the last 10 minutes."

      - alert: PaymentWebhookLagHigh
        expr: histogram_quantile(0.95, rate(webhook_lag_seconds_bucket[15m])) > 900
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Webhook processing is delayed (>15m p95)"
          description: "Webhook lag p95 stayed above 15 minutes for the last 15 minutes."
```

Adapt the thresholds to match production SLOs and wire them into Alertmanager with the usual on-call routing.
*** End Patch
