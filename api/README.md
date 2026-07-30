API Readme
====

## Stable native API

Native clients should use the versioned JSON API at `/api/v1`. Its complete
reference is [Mobile API v1](docs/Mobile_API_v1.md), is available in OSPy Help
as **Mobile API v1**, and has a machine-readable description at
`/api/v1/openapi.json`. It uses Bearer access tokens, rotating device refresh
tokens, scopes, 2FA and Server-Sent Events. The endpoints described below are
the older API and remain available for backward compatibility.

The proposal is to have a proper, modern web-API built on the CRUD principle using JSON as data-container format.
In HTML terms that means using the POST/GET/PUT/DELETE methods that mostly resemble Create, Read, Update and Delete.
For more - [RFC-2616](HTTP Method definitions http://tools.ietf.org/html/rfc2616.html#section-9).
These are the verbs (actions) that can be executed on nouns -- the objects of interest for us.
