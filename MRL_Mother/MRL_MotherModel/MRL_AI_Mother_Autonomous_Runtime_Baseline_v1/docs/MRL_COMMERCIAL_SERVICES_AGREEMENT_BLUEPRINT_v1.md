# MRL Commercial Services Agreement Blueprint v1

**Status:** contract-architecture blueprint; not represented as signed terms or jurisdiction-specific legal advice.  
**Canonical scope:** GitHub construction package + MRL model delivery + user-owned-hardware runtime + user-initiated return data.

## Evidence basis

This blueprint mirrors the clause architecture—not the copyrighted wording—of the current [OpenAI Services Agreement](https://openai.com/policies/services-agreement/), [Service Terms](https://openai.com/policies/service-terms/), [Data Processing Addendum](https://openai.com/policies/data-processing-addendum/) and [business data policy](https://openai.com/policies/how-your-data-is-used-to-improve-model-performance/), observed on 2026-08-27.

## Agreement stack and priority

1. Order Form: customer, model release, price, term, hardware support scope and selected return-data purpose.
2. Service-Specific Terms: model/runtime-specific restrictions and beta status.
3. MRL Commercial Services Agreement: general commercial relationship.
4. DPA: personal-data processing when returned files contain personal data.
5. Acceptable Use, Security and Model Documentation policies.

A future signed version must state which document controls in a conflict.

## Clause structure to draft

### 1. Parties, authority and effective date

Identify the contracting MRL entity and customer, authority to bind each entity, acceptance mechanism, effective date and incorporated Order Form. The final MRL contracting entity and governing jurisdiction are unresolved until supported by company evidence; this blueprint does not invent them.

### 2. Services and term

Define the service as access to the GitHub construction package, delivery of an identified MRL model release, compatibility documentation, updates and any purchased support. State initial term, renewal, quantities, authorized purchasers and affiliate use in the Order Form.

### 3. Model delivery and user-owned hardware

MRL supplies a model artifact and `MRL_Model_Release_v1` manifest. The customer verifies its SHA-256 before use and runs it on hardware the customer controls. The customer is responsible for hardware, electricity, network, backups, physical security, compatible drivers and local operation unless an Order Form expressly adds managed support. No named server or GPU is required by the canonical contract.

### 4. Customer obligations and restrictions

The customer must use the service lawfully, hold the rights needed for local inputs and returned files, protect credentials and model artifacts, follow documentation, and not bypass technical restrictions. Any restrictions on redistribution, reverse engineering, competing-model development, export, sanctions, safety controls or minors must be expressly stated and reviewed for the selected jurisdiction before release.

### 5. Customer content, local input and output

Use the following allocation model unless an Order Form says otherwise:

- the customer retains rights in its local Input;
- the customer owns local Output to the extent allowed by law;
- MRL retains all rights in the model, runtime, service and documentation;
- the customer grants MRL only the limited rights necessary to receive and process files that the customer deliberately returns for the stated purpose;
- similar or non-unique model outputs may occur;
- the customer evaluates output accuracy and suitability before relying on it.

### 6. Returned data and model improvement choice

Local Input, Output, Memory, Evidence and Passport records are not transferred merely because the software runs. Transfer occurs only when the customer creates and submits an `MRL_Return_Bundle_v1`.

Each bundle must record explicit consent, model release, hardware identifier, purpose, file list, size and SHA-256. The Order Form must distinguish at least:

1. support/diagnostics processing;
2. contracted service delivery;
3. security or abuse investigation where lawful;
4. optional product/model improvement.

Model-improvement use is off by default and requires a separate affirmative choice. Permission for one purpose does not authorize another purpose.

### 7. Security, privacy and DPA

State security measures for model delivery, return transport, access control, encryption, incident notice, audit evidence and subprocessors. If returned files contain personal data, incorporate a DPA specifying controller/processor roles, documented instructions, processing purpose, duration, data categories, data subjects, transfers, subprocessors, breach handling, return/deletion and audit rights.

### 8. Fees, invoices and taxes

Place price, currency, billing interval, model tier, support tier, usage metric, minimum commitment, credits and renewal in the Order Form. State invoice dispute timing, consequences of overdue amounts, refunds and responsibility for applicable taxes.

### 9. Confidentiality

Protect business, technical, financial, model and returned-file information; limit use to contract performance; allow disclosure only to need-to-know personnel and approved processors under equivalent duties; include standard public/prior-known/independently-developed exceptions and legally compelled disclosure procedure.

### 10. Suspension and security emergency

Allow narrowly tailored suspension for material breach, unlawful activity, compromised model artifacts, security emergency or overdue payment, with notice and restoration cooperation where reasonably possible.

### 11. Intellectual property and feedback

Reserve MRL ownership of the model, runtime, construction package, trademarks and documentation. Customer receives only the license stated in the Order Form. Separate returned Customer Content from optional Feedback; do not treat all returned files as unrestricted feedback.

### 12. Termination and data return/deletion

Define termination for uncured material breach, insolvency, nonpayment and any convenience right purchased in the Order Form. On termination, end model/service rights as specified, settle accrued fees, and return or delete provider-held returned data according to customer instruction and the retention schedule, except legally required or security-preservation copies.

### 13. Warranties, beta status and disclaimers

State any documentation-conformity warranty and support remedy. Clearly mark alpha/beta releases. Address model accuracy, non-unique output, customer-hardware failures, third-party components and fitness for high-risk use without promising capabilities not demonstrated by evidence.

### 14. Indemnification

Allocate third-party IP claims involving the supplied service, and customer claims arising from unlawful Input, returned files, customer applications or prohibited use. State exclusions for unauthorized modification, unsupported combinations, ignored safeguards and content the customer lacked rights to supply.

### 15. Limitation of liability

Define excluded indirect damages, the monetary cap and exceptions such as payment duties, confidentiality breach, indemnity, gross negligence, willful misconduct or security obligations. The amounts and enforceability must be selected for the governing law rather than copied from another provider.

### 16. Disputes, governing law and notices

Set informal-resolution steps, court or arbitration forum, governing law, venue, notice addresses and any class-action or jury-waiver terms only after the contracting entity and target customer jurisdictions are confirmed.

### 17. General terms and definitions

Include entire agreement, document priority, severability, waiver, assignment, independent contractors, force majeure, no third-party beneficiaries, trade controls, geographic limits, update notice and survival. Define Customer, End User, Input, Output, Customer Content, Returned Data, Model Release, User Hardware, Service, Documentation, Security Emergency, DPA and Order Form.

## Completion boundary

The clause map is complete for engineering and commercial design. A production contract remains `LEGAL_RELEASE_GATE_OPEN` until the contracting entity, governing law, pricing, license scope, retention period, receiving endpoint, subprocessors, security measures and dispute forum are fixed and reviewed for the intended market.
