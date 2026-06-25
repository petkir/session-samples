---
theme: default
layout: default
---

## Server‑Side Events (SSE)

```
export interface AssistantMessage {
    model: string;
    created_at: string; // ISO 8601 timestamp
    message: {
        role: string;
        content: string;
    };
    done: boolean;
    // optional summary/metrics (present on final chunk)
    done_reason?: string;
    total_duration?: number;
    load_duration?: number;
    prompt_eval_count?: number;
    prompt_eval_duration?: number;
    eval_count?: number;
    eval_duration?: number;
}

export type AssistantTranscript = AssistantMessage[];
```


