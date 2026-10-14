# Failure log

Every wrong output recorded with question, output, failure category, root cause. Categories: retrieval miss, bad chunking, ungrounded generation, guardrail false positive, guardrail false negative, other.

## Config: no guardrail
### q22 (answerable)
**Q:** Who must pay self-employment tax?
**Expected:** ['p334-se-tax'] | **Retrieved:** ['p334-business-income', 'p334-general', 'p334-are-you-self-employed', 'p334-se-tax', 'p334-general']
**Output:** Based on the IRS guides in my knowledge base [p334-business-income]: for services you perform as a notary public are reported on Schedule C (Form 1040) but are not subject to SE tax (see the Instructions for Schedule SE (Form 1040)). State or local government employee. You are subject to SE tax if you are an employee of a state or local government, are paid solely on a fee basis, and your services are not covered under a federal -state social security agreement. Foreign government or international organization employee. You are subject to SE tax if both the following conditions are true. 1. You are a U.S. citizen employed in the United States, Puerto Rico, Guam, American Samoa, the Commonwealth of the Northern Mariana Islands, or the U.S. Virgin Islands by: a. Aforeign government, b. Awhol
**Judge:** {"retrieval": 5, "groundedness": 4, "relevance": 2, "language": 5, "pass": false, "rationale": "heuristic: hit=True overlap=0.00 refusal=False", "backend": "heuristic"}
**Guard:** null
**Failure category:** ungrounded generation
**Root cause:** answer not supported by excerpts per judge

### q28 (answerable)
**Q:** What are the exclusive use and regular use tests for home office deduction?
**Expected:** ['p587-exclusive-regular-use', 'p587-home-use', 'p334-business-expenses-general'] | **Retrieved:** ['p334-general', 'p587-general', 'p587-general', 'p587-general', 'p334-general']
**Output:** Based on the IRS guides in my knowledge base [p334-general]: for business and for personal purposes. Example. Y ou are an attorney and use a den in your home to write legal briefs and prepare clients’ tax returns. Y our family also uses the den for recreation. The den is not used exclusively in your profession, so you can’t claim a business deduction for its use. Exceptions to exclusive use. Y ou don’t have to meet the exclusive use test to the extent you use part of your home in either of the following ways. 1. For the storage of inventory or product samples (for businesses in retail or wholesale trade with no other fixed location). 2. As a daycare facility. For an explanation of these exceptions, see Pub. 587, Business Use of Y our Home. Regular use. T o qualify under the regular use tes
**Judge:** {"retrieval": 2, "groundedness": 3, "relevance": 4, "language": 5, "pass": false, "rationale": "heuristic: hit=False overlap=0.57 refusal=False", "backend": "heuristic"}
**Guard:** null
**Failure category:** retrieval miss
**Root cause:** expected ['p587-exclusive-regular-use', 'p587-home-use', 'p334-business-expenses-general'] not in retrieved ['p334-general', 'p587-general', 'p587-general', 'p587-general', 'p334-general']

### q33 (answerable)
**Q:** Can daycare providers use their home for business even without exclusive use?
**Expected:** ['p587-exclusive-regular-use', 'p587-home-use', 'p334-business-expenses-general'] | **Retrieved:** ['p587-principal-place', 'p587-simplified-method', 'p587-actual-expenses', 'p334-general', 'p587-simplified-method']
**Output:** Based on the IRS guides in my knowledge base [p334-general]: for business and for personal purposes. Example. Y ou are an attorney and use a den in your home to write legal briefs and prepare clients’ tax returns. Y our family also uses the den for recreation. The den is not used exclusively in your profession, so you can’t claim a business deduction for its use. Exceptions to exclusive use. Y ou don’t have to meet the exclusive use test to the extent you use part of your home in either of the following ways. 1. For the storage of inventory or product samples (for businesses in retail or wholesale trade with no other fixed location). 2. As a daycare facility. For an explanation of these exceptions, see Pub. 587, Business Use of Y our Home. Regular use. T o qualify under the regular use tes
**Judge:** {"retrieval": 2, "groundedness": 3, "relevance": 4, "language": 5, "pass": false, "rationale": "heuristic: hit=False overlap=0.50 refusal=False", "backend": "heuristic"}
**Guard:** null
**Failure category:** retrieval miss
**Root cause:** expected ['p587-exclusive-regular-use', 'p587-home-use', 'p334-business-expenses-general'] not in retrieved ['p587-principal-place', 'p587-simplified-method', 'p587-actual-expenses', 'p334-general', 'p587-simplified-method']

### q43 (answerable)
**Q:** What about my spouse who helps part-time — same rule?
**Expected:** ['p334-se-tax', 'p334-are-you-self-employed'] | **Retrieved:** ['p334-are-you-self-employed', 'p334-general', 'p334-general', 'p334-are-you-self-employed', 'p334-general']
**Output:** Based on the IRS guides in my knowledge base [p334-are-you-self-employed]: ession in which they offer their services to the general public are generally independent contractors. However, whether they are independent contractors or employees depends on the facts in each case. The general rule is that an individual is an independent contractor if the person paying for the work has the right to control or to direct only the result of the work and not how it will be done. The earnings of a person who is working as an independent contractor are subject to self -employment tax. For more information on determining whether you are an employee or independent contractor, see Pub. 15 -A, Employer’s Supplemental Tax Guide. Are You a Statutory Employee? Astatutory employee has a checkmark in box 13 of 
**Judge:** {"retrieval": 5, "groundedness": 4, "relevance": 2, "language": 5, "pass": false, "rationale": "heuristic: hit=True overlap=0.12 refusal=False", "backend": "heuristic"}
**Guard:** null
**Failure category:** ungrounded generation
**Root cause:** answer not supported by excerpts per judge

## Config: Tier 1 only
### q22 (answerable)
**Q:** Who must pay self-employment tax?
**Expected:** ['p334-se-tax'] | **Retrieved:** ['p334-business-income', 'p334-general', 'p334-are-you-self-employed', 'p334-se-tax', 'p334-general']
**Output:** Based on the IRS guides in my knowledge base [p334-business-income]: for services you perform as a notary public are reported on Schedule C (Form 1040) but are not subject to SE tax (see the Instructions for Schedule SE (Form 1040)). State or local government employee. You are subject to SE tax if you are an employee of a state or local government, are paid solely on a fee basis, and your services are not covered under a federal -state social security agreement. Foreign government or international organization employee. You are subject to SE tax if both the following conditions are true. 1. You are a U.S. citizen employed in the United States, Puerto Rico, Guam, American Samoa, the Commonwealth of the Northern Mariana Islands, or the U.S. Virgin Islands by: a. Aforeign government, b. Awhol
**Judge:** {"retrieval": 5, "groundedness": 4, "relevance": 2, "language": 5, "pass": false, "rationale": "heuristic: hit=True overlap=0.00 refusal=False", "backend": "heuristic"}
**Guard:** {"tier1_score": 0.7574, "tier1_pass": true, "tier2_ran": false, "verdict": "pass"}
**Failure category:** ungrounded generation
**Root cause:** answer not supported by excerpts per judge

### q28 (answerable)
**Q:** What are the exclusive use and regular use tests for home office deduction?
**Expected:** ['p587-exclusive-regular-use', 'p587-home-use', 'p334-business-expenses-general'] | **Retrieved:** ['p334-general', 'p587-general', 'p587-general', 'p587-general', 'p334-general']
**Output:** Based on the IRS guides in my knowledge base [p334-general]: for business and for personal purposes. Example. Y ou are an attorney and use a den in your home to write legal briefs and prepare clients’ tax returns. Y our family also uses the den for recreation. The den is not used exclusively in your profession, so you can’t claim a business deduction for its use. Exceptions to exclusive use. Y ou don’t have to meet the exclusive use test to the extent you use part of your home in either of the following ways. 1. For the storage of inventory or product samples (for businesses in retail or wholesale trade with no other fixed location). 2. As a daycare facility. For an explanation of these exceptions, see Pub. 587, Business Use of Y our Home. Regular use. T o qualify under the regular use tes
**Judge:** {"retrieval": 2, "groundedness": 3, "relevance": 4, "language": 5, "pass": false, "rationale": "heuristic: hit=False overlap=0.57 refusal=False", "backend": "heuristic"}
**Guard:** {"tier1_score": 0.6986, "tier1_pass": true, "tier2_ran": false, "verdict": "pass"}
**Failure category:** retrieval miss
**Root cause:** expected ['p587-exclusive-regular-use', 'p587-home-use', 'p334-business-expenses-general'] not in retrieved ['p334-general', 'p587-general', 'p587-general', 'p587-general', 'p334-general']

### q33 (answerable)
**Q:** Can daycare providers use their home for business even without exclusive use?
**Expected:** ['p587-exclusive-regular-use', 'p587-home-use', 'p334-business-expenses-general'] | **Retrieved:** ['p587-principal-place', 'p587-simplified-method', 'p587-actual-expenses', 'p334-general', 'p587-simplified-method']
**Output:** Based on the IRS guides in my knowledge base [p334-general]: for business and for personal purposes. Example. Y ou are an attorney and use a den in your home to write legal briefs and prepare clients’ tax returns. Y our family also uses the den for recreation. The den is not used exclusively in your profession, so you can’t claim a business deduction for its use. Exceptions to exclusive use. Y ou don’t have to meet the exclusive use test to the extent you use part of your home in either of the following ways. 1. For the storage of inventory or product samples (for businesses in retail or wholesale trade with no other fixed location). 2. As a daycare facility. For an explanation of these exceptions, see Pub. 587, Business Use of Y our Home. Regular use. T o qualify under the regular use tes
**Judge:** {"retrieval": 2, "groundedness": 3, "relevance": 4, "language": 5, "pass": false, "rationale": "heuristic: hit=False overlap=0.50 refusal=False", "backend": "heuristic"}
**Guard:** {"tier1_score": 0.7304, "tier1_pass": true, "tier2_ran": false, "verdict": "pass"}
**Failure category:** retrieval miss
**Root cause:** expected ['p587-exclusive-regular-use', 'p587-home-use', 'p334-business-expenses-general'] not in retrieved ['p587-principal-place', 'p587-simplified-method', 'p587-actual-expenses', 'p334-general', 'p587-simplified-method']

### q43 (answerable)
**Q:** What about my spouse who helps part-time — same rule?
**Expected:** ['p334-se-tax', 'p334-are-you-self-employed'] | **Retrieved:** ['p334-are-you-self-employed', 'p334-general', 'p334-general', 'p334-are-you-self-employed', 'p334-general']
**Output:** Based on the IRS guides in my knowledge base [p334-are-you-self-employed]: ession in which they offer their services to the general public are generally independent contractors. However, whether they are independent contractors or employees depends on the facts in each case. The general rule is that an individual is an independent contractor if the person paying for the work has the right to control or to direct only the result of the work and not how it will be done. The earnings of a person who is working as an independent contractor are subject to self -employment tax. For more information on determining whether you are an employee or independent contractor, see Pub. 15 -A, Employer’s Supplemental Tax Guide. Are You a Statutory Employee? Astatutory employee has a checkmark in box 13 of 
**Judge:** {"retrieval": 5, "groundedness": 4, "relevance": 2, "language": 5, "pass": false, "rationale": "heuristic: hit=True overlap=0.12 refusal=False", "backend": "heuristic"}
**Guard:** {"tier1_score": 0.6802, "tier1_pass": true, "tier2_ran": false, "verdict": "pass"}
**Failure category:** ungrounded generation
**Root cause:** answer not supported by excerpts per judge

## Config: Tier 1 + Tier 2
### q22 (answerable)
**Q:** Who must pay self-employment tax?
**Expected:** ['p334-se-tax'] | **Retrieved:** ['p334-business-income', 'p334-general', 'p334-are-you-self-employed', 'p334-se-tax', 'p334-general']
**Output:** Based on the IRS guides in my knowledge base [p334-business-income]: for services you perform as a notary public are reported on Schedule C (Form 1040) but are not subject to SE tax (see the Instructions for Schedule SE (Form 1040)). State or local government employee. You are subject to SE tax if you are an employee of a state or local government, are paid solely on a fee basis, and your services are not covered under a federal -state social security agreement. Foreign government or international organization employee. You are subject to SE tax if both the following conditions are true. 1. You are a U.S. citizen employed in the United States, Puerto Rico, Guam, American Samoa, the Commonwealth of the Northern Mariana Islands, or the U.S. Virgin Islands by: a. Aforeign government, b. Awhol
**Judge:** {"retrieval": 5, "groundedness": 4, "relevance": 2, "language": 5, "pass": false, "rationale": "heuristic: hit=True overlap=0.00 refusal=False", "backend": "heuristic"}
**Guard:** {"tier1_score": 0.7574, "tier1_threshold": 0.28, "tier1_pass": true, "tier1_best_window": "tax if you are an employee of a state or local government, are paid solely on a fee basis, and your services are not covered under a federal -state social security agreement. Foreign government or int", "tier2_ran": false, "tier2_pass": null, "tier2_rationale": "", "verdict": "pass", "latency_s": 0.013}
**Failure category:** ungrounded generation
**Root cause:** answer not supported by excerpts per judge

### q28 (answerable)
**Q:** What are the exclusive use and regular use tests for home office deduction?
**Expected:** ['p587-exclusive-regular-use', 'p587-home-use', 'p334-business-expenses-general'] | **Retrieved:** ['p334-general', 'p587-general', 'p587-general', 'p587-general', 'p334-general']
**Output:** Based on the IRS guides in my knowledge base [p334-general]: for business and for personal purposes. Example. Y ou are an attorney and use a den in your home to write legal briefs and prepare clients’ tax returns. Y our family also uses the den for recreation. The den is not used exclusively in your profession, so you can’t claim a business deduction for its use. Exceptions to exclusive use. Y ou don’t have to meet the exclusive use test to the extent you use part of your home in either of the following ways. 1. For the storage of inventory or product samples (for businesses in retail or wholesale trade with no other fixed location). 2. As a daycare facility. For an explanation of these exceptions, see Pub. 587, Business Use of Y our Home. Regular use. T o qualify under the regular use tes
**Judge:** {"retrieval": 2, "groundedness": 3, "relevance": 4, "language": 5, "pass": false, "rationale": "heuristic: hit=False overlap=0.57 refusal=False", "backend": "heuristic"}
**Guard:** {"tier1_score": 0.6986, "tier1_threshold": 0.28, "tier1_pass": true, "tier1_best_window": "for business and for personal purposes. Example. Y ou are an attorney and use a den in your home to write legal briefs and prepare clients\u2019 tax returns. Y our family also uses the den for recreation. ", "tier2_ran": false, "tier2_pass": null, "tier2_rationale": "", "verdict": "pass", "latency_s": 0.018}
**Failure category:** retrieval miss
**Root cause:** expected ['p587-exclusive-regular-use', 'p587-home-use', 'p334-business-expenses-general'] not in retrieved ['p334-general', 'p587-general', 'p587-general', 'p587-general', 'p334-general']

### q33 (answerable)
**Q:** Can daycare providers use their home for business even without exclusive use?
**Expected:** ['p587-exclusive-regular-use', 'p587-home-use', 'p334-business-expenses-general'] | **Retrieved:** ['p587-principal-place', 'p587-simplified-method', 'p587-actual-expenses', 'p334-general', 'p587-simplified-method']
**Output:** Based on the IRS guides in my knowledge base [p334-general]: for business and for personal purposes. Example. Y ou are an attorney and use a den in your home to write legal briefs and prepare clients’ tax returns. Y our family also uses the den for recreation. The den is not used exclusively in your profession, so you can’t claim a business deduction for its use. Exceptions to exclusive use. Y ou don’t have to meet the exclusive use test to the extent you use part of your home in either of the following ways. 1. For the storage of inventory or product samples (for businesses in retail or wholesale trade with no other fixed location). 2. As a daycare facility. For an explanation of these exceptions, see Pub. 587, Business Use of Y our Home. Regular use. T o qualify under the regular use tes
**Judge:** {"retrieval": 2, "groundedness": 3, "relevance": 4, "language": 5, "pass": false, "rationale": "heuristic: hit=False overlap=0.50 refusal=False", "backend": "heuristic"}
**Guard:** {"tier1_score": 0.7304, "tier1_threshold": 0.28, "tier1_pass": true, "tier1_best_window": "for business and for personal purposes. Example. Y ou are an attorney and use a den in your home to write legal briefs and prepare clients\u2019 tax returns. Y our family also uses the den for recreation. ", "tier2_ran": false, "tier2_pass": null, "tier2_rationale": "", "verdict": "pass", "latency_s": 0.01}
**Failure category:** retrieval miss
**Root cause:** expected ['p587-exclusive-regular-use', 'p587-home-use', 'p334-business-expenses-general'] not in retrieved ['p587-principal-place', 'p587-simplified-method', 'p587-actual-expenses', 'p334-general', 'p587-simplified-method']

### q43 (answerable)
**Q:** What about my spouse who helps part-time — same rule?
**Expected:** ['p334-se-tax', 'p334-are-you-self-employed'] | **Retrieved:** ['p334-are-you-self-employed', 'p334-general', 'p334-general', 'p334-are-you-self-employed', 'p334-general']
**Output:** Based on the IRS guides in my knowledge base [p334-are-you-self-employed]: ession in which they offer their services to the general public are generally independent contractors. However, whether they are independent contractors or employees depends on the facts in each case. The general rule is that an individual is an independent contractor if the person paying for the work has the right to control or to direct only the result of the work and not how it will be done. The earnings of a person who is working as an independent contractor are subject to self -employment tax. For more information on determining whether you are an employee or independent contractor, see Pub. 15 -A, Employer’s Supplemental Tax Guide. Are You a Statutory Employee? Astatutory employee has a checkmark in box 13 of 
**Judge:** {"retrieval": 5, "groundedness": 4, "relevance": 2, "language": 5, "pass": false, "rationale": "heuristic: hit=True overlap=0.12 refusal=False", "backend": "heuristic"}
**Guard:** {"tier1_score": 0.6802, "tier1_threshold": 0.28, "tier1_pass": true, "tier1_best_window": "contractor if the person paying for the work has the right to control or to direct only the result of the work and not how it will be done. The earnings of a person who is working as an independent co", "tier2_ran": false, "tier2_pass": null, "tier2_rationale": "", "verdict": "pass", "latency_s": 0.014}
**Failure category:** ungrounded generation
**Root cause:** answer not supported by excerpts per judge

## Summary (counts by config x category)

- none x retrieval miss: 2
- none x ungrounded generation: 2
- tier1 x retrieval miss: 2
- tier1 x ungrounded generation: 2
- tier1+2 x retrieval miss: 2
- tier1+2 x ungrounded generation: 2
