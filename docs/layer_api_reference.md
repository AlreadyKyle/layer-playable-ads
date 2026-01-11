# Layer.ai API Reference

**Last Updated**: 2025-01-11
**API Endpoint**: `https://api.app.layer.ai/graphql`
**Authentication**: Bearer token via `Authorization` header

---

## Overview

Layer.ai uses a GraphQL API. All operations require authentication with a Personal Access Token (PAT).

**CRITICAL**: Layer.ai generates images using **trained styles** (LoRAs/checkpoints). You cannot generate images with just text prompts - you must provide a `styleId` from a pre-trained style.

---

## Authentication

Use a Personal Access Token (PAT) as a Bearer token:

```python
headers = {
    "Authorization": f"Bearer {LAYER_API_KEY}",
    "Content-Type": "application/json",
}
```

Get your PAT at: [app.layer.ai](https://app.layer.ai) → Settings → API Keys

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

**Style Types**:
- `MODEL_URL` - Base AI models (FLUX, Kling, etc.) - may have generation restrictions
- `LAYER_TRAINED_CHECKPOINT` - Custom styles you train with your images
- `UPLOADED_CHECKPOINT` / `UPLOADED_LORA` - Models you upload

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

Fetch available styles. Returns a **Relay-style connection** with `edges/node` pattern.

**IMPORTANT**: `StylesResponse` is a UNION type with `StylesConnection | Error`. Use `StylesConnection` (not `StylesResult`).

```graphql
query ListStyles($input: ListStylesInput!) {
    listStyles(input: $input) {
        __typename
        ... on StylesConnection {
            edges {
                node {
                    id
                    name
                    status
                    type
                }
            }
            pageInfo {
                hasNextPage
                endCursor
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
        "first": 50
    }
}
```

**ListStylesInput Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `first` | Int | Number of styles to fetch (pagination) |
| `last` | Int | Fetch last N styles |
| `after` | String | Cursor for forward pagination |
| `before` | String | Cursor for backward pagination |
| `status` | [StyleStatus] | Filter by status (e.g., ["COMPLETE"]) |
| `visibility` | StyleVisibility | Filter by visibility |
| `topics` | [String] | Filter by topics |
| `isFeatured` | Boolean | Filter featured styles |

**Note**: `workspaceId` is NOT required - styles are determined by your API token.

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
        "inferenceIds": ["inference-id-here"]
    }
}
```

**Note**: The field is `inferenceIds` (not `ids`).

### Get Workspace Usage

Check available credits.

```graphql
query GetWorkspaceUsage($input: GetWorkspaceUsageInput!) {
    getWorkspaceUsage(input: $input) {
        __typename
        ... on WorkspaceUsage {
            entitlement {
                balance
                hasAccess
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
        "filtering": []
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

### StyleStatus

```
TRAINING     - Style is being trained
COMPLETE     - Style is ready to use
FAILED       - Style training failed
```

### StyleType

```
LAYER_TRAINED_CHECKPOINT  - Style trained by Layer.ai
UPLOADED_CHECKPOINT       - User-uploaded checkpoint
UPLOADED_LORA            - User-uploaded LoRA
MODEL_URL                - External model URL (base models like FLUX, Kling)
```

---

## Error Handling

Layer.ai uses **union types** for responses. Always check `__typename`:

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
| "Oops! Our pixel wizards need a moment..." | Rate limit or server issue | Wait and retry |
| "Cannot query field 'styles' on type 'StylesResponse'" | Wrong union type | Use `StylesConnection` with `edges/node` |
| "Cannot query field 'X'" | Field doesn't exist | Verify field names via introspection |
| HTTP 401 | Invalid API key | Check `LAYER_API_KEY` |
| HTTP 403 | No workspace access | Check `LAYER_WORKSPACE_ID` |

---

## Relay Connection Pattern

Layer.ai uses [Relay-style pagination](https://relay.dev/graphql/connections.htm) for list queries:

```graphql
... on StylesConnection {
    edges {
        node {
            id
            name
            # ... other fields
        }
        cursor
    }
    pageInfo {
        hasNextPage
        hasPreviousPage
        startCursor
        endCursor
    }
}
```

**Parsing in Python:**
```python
result = data.get("listStyles", {})
edges = result.get("edges", [])
styles = [edge.get("node") for edge in edges if edge.get("node")]
```

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
3. **Prefer custom trained styles** - `MODEL_URL` types are base models and may have restrictions
4. **Poll with backoff** - start at 2s, increase to max 10s
5. **Handle union types** - always check `__typename` in responses
6. **Set reasonable timeouts** - generation typically takes 10-60 seconds
7. **Use Relay pagination** - extract data from `edges[].node`

---

## Introspection Queries

Use these to explore the schema at `https://api.app.layer.ai/graphql`:

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

### Check union types
```graphql
{
    __type(name: "UnionTypeName") {
        possibleTypes {
            name
            fields { name }
        }
    }
}
```

---

## Discovered Schema Details

Through introspection, we found:

### ListStylesInput
```
topics: [String]
isFeatured: Boolean
status: [StyleStatus]
visibility: StyleVisibility
after: String
before: String
first: Int
last: Int
```

### StylesResponse (UNION)
```
possibleTypes:
  - StylesConnection (has: pageInfo, edges)
  - Error (has: type, code, title, message, data)
```

### GetInferencesByIdInput
```
inferenceIds: [ID!]!
```

### GetWorkspaceUsageInput
```
workspaceId: ID!
filtering: [WorkspaceUsageFilter!]!
```

---

## Limitations

1. **No text-only generation** - Must have a trained style
2. **Style training is async** - New styles take time to train
3. **Rate limits apply** - "pixel wizards need to recharge" error indicates rate limiting
4. **Credits consumed per generation** - Monitor workspace credits
5. **MODEL_URL styles may have restrictions** - Custom trained styles are more reliable
