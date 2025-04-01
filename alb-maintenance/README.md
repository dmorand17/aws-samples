# ALB Maintenance window

**conditions.json**

```json
[
  {
    "Field": "path-pattern",
    "Values": ["/*"]
  }
]
```

**actions.json**

```json
[
  {
    "Type": "fixed-response",
    "FixedResponseConfig": {
      "StatusCode": "503",
      "ContentType": "text/html",
      "MessageBody": "<html><body><h1>Service Temporarily Unavailable</h1><p>We are performing scheduled maintenance. Please check back later.</p></body></html>"
    }
  }
]
```

```bash
aws elbv2 create-rule --listener-arn <listener-arn> --priority 1 --conditions file://conditions.json --actions file://actions.json

```

Stop DCV connection gateway

```bash
systemctl stop dcv-connection-gateway.service
```
