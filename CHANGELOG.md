# CHANGELOG

<!--- next entry here -->

## 2.9.3
2025-07-17

### Fixes

- declare version 2.9.2; use sw360 ^1.10.0; update poetry.lock (04a61150628746eeff74e5f270ff6d2d19e2d283)

## 2.6.0
2024-11-11

### Features

- extend and cleanup the granularity list (7d86fb9f0b4fdce0ebed8cf1366f1750227e1235)
- prevent uploading .git files (42e0eeb90573f957d0f3941057ef0a05d014df7a)
- support CycloneDX 1.6 - make all tests work again (893a2074fa9fea4b62fc55dffe7e208dc93cf6b7)
- make findsources more resilient against SW360 issues (8a340452bc2ee5f3395cae1650096be1389f6058)
- update cyclonedx_python_lib to version 8.3.0 (d49573c2c28c2535df3ff3396bd8a44c6bd276b7)
- add standard-bom as definitions/standard (56a15016b8a87478fe5ae84f82058cd7100930b0)
- use siemens:profile `clearing` (1ee05473ad9fdddcb5bb890a1e0fb0ef794dc90a)
- dependency updates (69ef3c96d84ed674fe20098494a7a3799e0236f7)
- `getdependencies python` can now detect and ignore dev dependencies also for new versions of the `poetry.lock` file (e63784313aeeab31113e1df442120ea482db7b8a)
- release 2.6.0.dev1 (7334e7a109eec94525535a37b88821e946509421)
- ensure that a filtered SBOM contains the standard BOM definition (6d14db1ffa6d5062e3f798b7e9c796e91d12fc25)
- `bom merge` improved: the dependencies are reconstructed (ab697e1cdbac148a7ce73f876cebeff51e1f9dde)

### Fixes

- add pipeline (f497d74b91345a0782ccfe4ee1db5cc9d2dcc630)
- rpm handling and github interaction (a9cbbe1c5ab9ae517e6e3c10c6c5d81d7e09b007)
- **project createbom:** store multiple purls in property "purl_list" (61e8b87e7b2ab3d6df523addedd3ff62e32e732c)
- cleanup logs (e23beaeb6d4b42bc7f784c789a0d3cda0a9a64f0)
- ensure filename is not none (f8e9154b89130a4a3c033284da974e7854b7a436)
- suüpress cyclonedx-python-lib warnings (84537873cdfebe59d80c0eebcd4b54eb8001cb67)
- exclude blocking tests (60af95e1e2ea0bbbb4311938da1e851a49f8c21c)
- have specific tests for CycloneDX SBOM features (a4994fd38ecc236b0edd065d5e4fbcc9de703639)
- update changelog (f6f377480d59151fa6786b466b8aa39fe567050c)
- add documentation for SBOM filtering (8fdaa054ea64b0f1569526047be2db3e0f95a560)
- update changelog (f1ad3f43d0e4098cb38f617009ca7475d4a886df)
- update poetry.lock (7100a1463bccb3fc93b9a2285dbd65723d248135)