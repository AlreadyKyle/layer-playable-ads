# Layer.ai API Reference

**Last Updated**: 2025-01-11
**API Endpoint**: `https://api.app.layer.ai/v1/graphql`
**Authentication**: Bearer token via `Authorization` header

---

## Overview

Layer.ai uses a GraphQL API. All operations require authentication with an API key and a workspace ID.

**CRITICAL**: Layer.ai generates images using **trained styles** (LoRAs/checkpoints). You cannot generate images with just text prompts - you must provide a `styleId` from a pre-trained style.

---

## Authentication

```python
headers = {
    "Authorization": f"Bearer {LAYER_API_KEY}",
    "Content-Type": "application/json",
}
```

---

## Core Concepts

### Styles

Styles are trained ML models that define the visual appearance of generated images.

| Field | Type | Description |
|-------|------|-------------|
| `id` | ID! | Unique identifier |
| `name` | String | Human-readable name |
| `status` | StyleStatus | TRAINING, COMPLETE, FAILED |
| `type` | StyleType | LAYER_TRAINED_CHECKPOINT, UPLOADED_CHECKPOINT, UPLOADED_LORA, MODEL_URL |

**IMPORTANT**: Only styles with `status: "COMPLETE"` can be used for generation.

### Inferences (Image Generation)

When you generate images, Layer.ai creates an "Inference" that processes asynchronously.

| Field | Type | Description |
|-------|------|-------------|
| `id` | ID! | Inference identifier (use for polling) |
| `status` | InferenceStatus | IN_PROGRESS, COMPLETE, FAILED, CANCELLED, DELETED |
| `files` | [File!] | Generated image files |
| `errorCode` | String | Error details if failed |

### Files

Generated images are returned as File objects.

| Field | Type | Description |
|-------|------|-------------|
| `id` | ID! | File identifier |
| `status` | FileStatus | Processing status |
| `url` | String | Direct URL to the image |
| `previewUrl` | String | Preview/thumbnail URL |
| `width` | Int | Image width in pixels |
| `height` | Int | Image height in pixels |

---

## Queries

### List Styles

Fetch available styles in a workspace.

```graphql
query ListStyles($input: ListStylesInput!) {
    listStyles(input: $input) {
        __typename
        ... on StylesResult {
            styles {
                id
                name
                status
                type
            }
            pageInfo {
                hasNextPage
            }
        }
        ... on Error {
            code
            message
        }
    }
}
```

**Variables:**
```json
{
    "input": {
        "workspaceId": "your-workspace-id",
        "first": 50
    }
}
```

### Get Inference Status

Poll for generation completion.

```graphql
query GetInferencesById($input: GetInferencesByIdInput!) {
    getInferencesById(input: $input) {
        __typename
        ... on InferencesResult {
            inferences {
                id
                status
                errorCode
                files {
                    id
                    status
                    url
                }
            }
        }
        ... on Error {
            code
            message
        }
    }
}
```

**Variables:**
```json
{
    "input": {
        "ids": ["inference-id-here"]
    }
}
```

### Get Workspace Info

Check available credits.

```graphql
query GetWorkspace($workspaceId: ID!) {
    workspace(id: $workspaceId) {
        id
        name
        credits {
            available
            used
            total
        }
    }
}
```

---

## Mutations

### Generate Images

**CRITICAL**: `styleId` is REQUIRED even though the schema marks it as optional.

```graphql
mutation GenerateImages($input: GenerateImagesInput!) {
    generateImages(input: $input) {
        __typename
        ... on Inference {
            id
            status
            files {
                id
                status
                url
            }
        }
        ... on Error {
            type
            code
            message
        }
    }
}
```

**Variables:**
```json
{
    "input": {
        "workspaceId": "your-workspace-id",
        "styleId": "style-id-here",
        "prompt": "your generation prompt"
    }
}
```

#### GenerateImagesInput Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `workspaceId` | ID! | Yes | Workspace identifier |
| `styleId` | ID | **Yes*** | Style to use for generation |
| `prompt` | String | No | Text prompt for generation |
| `batchSize` | Int | No | Number of images to generate |
| `seed` | Long | No | Random seed for reproducibility |
| `width` | Int | No | Output width |
| `height` | Int | No | Output height |
| `numInferenceSteps` | Int | No | Quality vs speed tradeoff |
| `guidanceScale` | Float | No | How closely to follow prompt |

*Even though schema shows optional, API returns error "At least one style must be provided" without it.

---

## Enums

### InferenceStatus

```
IN_PROGRESS  - Generation is running
COMPLETE     - Generation finished successfully
FAILED       - Generation failed
CANCELLED    - Generation was cancelled
DELETED      - Inference was deleted
```

### StyleType

```
LAYER_TRAINED_CHECKPOINT  - Style trained by Layer.ai
UPLOADED_CHECKPOINT       - User-uploaded checkpoint
UPLOADED_LORA            - User-uploaded LoRA
MODEL_URL                - External model URL
```

---

## Error Handling

Layer.ai uses union types for responses. Always check `__typename`:

```python
result = data.get("generateImages", {})

if result.get("__typename") == "Error":
    error_msg = result.get("message", "Unknown error")
    raise LayerAPIError(f"Generation failed: {error_msg}")

# Otherwise, it's a successful Inference
inference_id = result.get("id")
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "At least one style must be provided" | Missing `styleId` | Always include `styleId` in input |
| "Unknown type 'X'" | Wrong input type name | Check exact GraphQL type names |
| "Cannot query field 'X'" | Field doesn't exist | Verify field names via introspection |
| HTTP 401 | Invalid API key | Check `LAYER_API_KEY` |
| HTTP 403 | No workspace access | Check `LAYER_WORKSPACE_ID` |

---

## Polling Pattern

Generation is asynchronous. Poll for completion:

```python
async def poll_generation(inference_id: str, timeout: float = 120.0):
    start_time = time.time()
    interval = 2.0

    while time.time() - start_time < timeout:
        result = await get_inference_status(inference_id)

        if result.status == "COMPLETE":
            return result
        elif result.status == "FAILED":
            raise GenerationError(result.error_code)

        await asyncio.sleep(interval)
        interval = min(interval * 1.5, 10.0)  # Backoff

    raise TimeoutError("Generation timed out")
```

---

## Best Practices

1. **Always check credits** before starting generation
2. **Use trained styles only** - status must be "COMPLETE"
3. **Poll with backoff** - start at 2s, increase to max 10s
4. **Handle union types** - always check `__typename` in responses
5. **Set reasonable timeouts** - generation typically takes 10-60 seconds

---

## Introspection Queries

Use these to explore the schema:

### Get type fields
```graphql
{
    __type(name: "TypeName") {
        fields {
            name
            type { name kind }
        }
    }
}
```

### Get input fields
```graphql
{
    __type(name: "InputTypeName") {
        inputFields {
            name
            type { name kind ofType { name kind } }
        }
    }
}
```

### Get enum values
```graphql
{
    __type(name: "EnumName") {
        enumValues { name }
    }
}
```

---

## Limitations

1. **No text-only generation** - Must have a trained style
2. **Style training is async** - New styles take time to train
3. **Rate limits apply** - Check with Layer.ai for limits
4. **Credits consumed per generation** - Monitor workspace credits
