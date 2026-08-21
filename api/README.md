API Readme
====

## Stable native API

Native clients should use the versioned JSON API at `/api/v1`. Its complete reference is [Mobile API v1](docs/Mobile_API_v1.md), is available in OSPy Help as **Mobile API v1**, and has a machine-readable description at `/api/v1/openapi.json`. It uses Bearer access tokens, rotating device refresh tokens, scopes, 2FA and Server-Sent Events. The endpoints described below are the older API and remain available for backward compatibility.

Monitoring plug-ins can expose cached measurements through the internal, JSON-safe [plug-in provider contract v1](docs/Provider_Contract_v1.md). The contract is read-only in Stage 1 and is intended for Automation Rules and Irrigation Safety; it does not replace existing plug-in pages or Mobile API contributions.

Mobile login applies the same account-specific 2FA as the web interface. The built-in administrator retains the original global settings; each additional user can independently use TOTP, e-mail verification and one-time backup codes.

The native API also supports installation-scoped immediate push delivery through `GET/POST/PUT/DELETE /api/v1/push` and `POST /api/v1/push/test`. Push is disabled by default and the administrator may edit the prefilled official relay URL. OSPy keeps no Firebase credential or FCM token: it signs an asynchronous request to the configured HTTPS relay. A client that sends the persistent ID of an existing device during login replaces that device's token session without creating a duplicate paired-device row. See [Immediate push notifications](docs/Mobile_API_v1.md#immediate-push-notifications) for the mobile registration flow, relay contract and security boundaries.

Mobile API v1 exposes the user and effective water-level adjustments through `/irrigation`, preserves and validates `group_id` in complete and partial program updates, lists native program groups through `/program-groups` and supports creating or cancelling the same one-time group postponements as the OSPy Programs page. Refresh-token rotation is safe for concurrent mobile clients: access tokens already issued for the same rotating session remain valid until their short expiry, while logout, renewed pairing and device revocation still invalidate access immediately.

The proposal is to have a proper, modern web-API built on the CRUD principle using JSON as data-container format.
In HTML terms that means using the POST/GET/PUT/DELETE methods that mostly resemble Create, Read, Update and Delete.
For more - [RFC-2616](HTTP Method definitions http://tools.ietf.org/html/rfc2616.html#section-9).
These are the verbs (actions) that can be executed on nouns -- the objects of interest for us.
