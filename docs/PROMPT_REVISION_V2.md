# 🎯 MAJOR PROMPT REVISION V2 - More Inclusive Classification

## 📅 Date: October 26, 2025

---

## 🔄 **PHILOSOPHY SHIFT: From "ND-Specific" to "Helps ND People"**

### **BEFORE (Too Narrow):**
❌ "Is this service SPECIFICALLY DESIGNED for neurodivergent people?"
- Missed valuable resources like mental health services, crisis support, parent groups
- Focused only on services explicitly branded as "autism" or "ADHD"

### **AFTER (More Inclusive):**
✅ "Would a neurodivergent person or their family find this resource valuable?"
- Includes services that HELP ND people (not just ND-specific)
- Recognizes co-occurring conditions (mental health, crisis)
- Includes parent/carer support as part of ND ecosystem

---

## 🆕 **NEW SERVICE CATEGORIES NOW INCLUDED AS MEDIUM:**

### **1. Mental Health Services**
- **Why:** 70% of autistic people have co-occurring mental health conditions
- **Examples:** Anxiety counseling, depression therapy, trauma support
- **Previous score:** LOW (not ND-specific)
- **New score:** MEDIUM (significantly helps ND people)

### **2. Crisis Support Services**
- **Why:** Autistic people 9x higher suicide risk, ADHD 5x higher suicide attempts
- **Examples:** Samaritans, crisis helplines, emotional support hotlines
- **Previous score:** LOW (general service)
- **New score:** MEDIUM (critical for ND community)

### **3. Parent/Carer Support Groups**
- **Why:** Essential part of ND ecosystem, support families of ND children
- **Examples:** Parent Carer Forums, SEND parent groups, sibling support
- **Previous score:** LOW (not direct ND service)
- **New score:** MEDIUM (helps ND families)

### **4. Therapeutic Services (Generic)**
- **Why:** Commonly accessed by ND individuals
- **Examples:** Occupational Therapy, Speech & Language Therapy, Music Therapy
- **Previous score:** LOW (not ND-specific)
- **New score:** MEDIUM (frequently used by ND people)

### **5. Social Skills & Life Skills Training**
- **Why:** Directly addresses ND challenges
- **Examples:** Social skills groups, independence programs, life skills training
- **Previous score:** LOW if not branded as "autism social skills"
- **New score:** MEDIUM (helps ND people develop skills)

### **6. Employment & Benefits Support**
- **Why:** ND people face employment challenges and need benefit support
- **Examples:** Job coaching for disabled, supported employment, benefits advice
- **Previous score:** LOW (generic disability)
- **New score:** MEDIUM (helps ND people navigate systems)

### **7. Respite Care & Short Breaks**
- **Why:** Critical for families of ND children
- **Examples:** Respite care, short breaks, holiday clubs for SEND
- **Previous score:** LOW or varied
- **New score:** MEDIUM (essential family support)

---

## 📊 **REVISED SCORING FRAMEWORK:**

| Score | Meaning | Practical Test | Include in Directory? |
|-------|---------|----------------|----------------------|
| **HIGH** | **Primary ND Service** | "Would someone seek this OUT for ND support specifically?" | ✅ Yes |
| **MEDIUM** | **Significantly Helps ND** | "Would an ND family find this valuable in an ND directory?" | ✅ Yes |
| **LOW** | **Minimal ND Benefit** | "Generic service, not useful in ND directory" | ❌ No |
| **NONE** | **Not Relevant** | "No connection to ND needs" | ❌ No |

---

## ✅ **NEW RECOGNITION PATTERNS (ALWAYS MEDIUM or Higher):**

- ✅ SEND/SEN services (includes autism, ADHD, dyslexia)
- ✅ Autism-friendly, sensory-friendly, ND-friendly sessions
- ✅ **Mental health services** (anxiety, depression, trauma)
- ✅ **Crisis support** (helplines, suicide prevention)
- ✅ **Parent/carer support groups** (SEND families)
- ✅ **Therapeutic services** (OT, speech, hydrotherapy, music/art therapy)
- ✅ RDA and disability charities
- ✅ **Social skills, life skills programs**
- ✅ **Employment support for disabled**
- ✅ Special needs playgrounds, sensory facilities
- ✅ **Benefits advice, housing support for SEND**
- ✅ **Respite care, short breaks**

---

## ❌ **ALWAYS LOW or NONE:**

- ❌ Transport services (TfL, buses)
- ❌ Councils (general local authorities)
- ❌ Pharmacies, dentists, opticians (unless ND-specialist)
- ❌ Museums with only passive "quiet hours"
- ❌ Generic gyms, sports clubs (no adaptive programs)
- ❌ Schools without SEN provision
- ❌ Administrative offices (SEND offices that don't provide direct support)

---

## 🧪 **NEW EXAMPLES ADDED TO PROMPT:**

### **Example 3: Mental Health Counseling**
```
Service: "Mental Health Counseling Service (anxiety, depression, trauma)"
Score: MEDIUM
is_neurodivergent_related: true
Rationale: "70% of autistic people and 50% of ADHD adults have co-occurring mental health conditions"
```

### **Example 3b: Crisis Support**
```
Service: "Samaritans Crisis Helpline"
Score: MEDIUM
is_neurodivergent_related: true
Rationale: "Autistic people have 9x higher suicide rates, ADHD 5x higher suicide attempts"
```

### **Example 3c: Parent Support**
```
Service: "Parent Carer Forum for SEND Families"
Score: MEDIUM
is_neurodivergent_related: true
Rationale: "Supports families of ND children with peer support and information"
```

### **Example 11: Occupational Therapy**
```
Service: "Occupational Therapy Service (pediatric, general)"
Score: MEDIUM
is_neurodivergent_related: true
Rationale: "Frequently used by autistic and ADHD individuals for sensory processing"
```

### **Example 12: Speech Therapy**
```
Service: "Speech and Language Therapy Clinic"
Score: MEDIUM
is_neurodivergent_related: true
Rationale: "Frequently accessed by autistic children for communication development"
```

---

## 🎯 **NEW DECISION FRAMEWORK:**

1. **Does it explicitly mention SEND/SEN/autism/ADHD/dyslexia?** → HIGH or MEDIUM
2. **Is it mental health/crisis/parent support?** → MEDIUM (ND people have high co-morbidity)
3. **Is it therapeutic/adaptive (OT, speech, hydrotherapy)?** → MEDIUM
4. **Is it a general service everyone uses?** → LOW or NONE
5. **WHEN UNSURE:** Ask "Would an ND family find this in an ND directory?" If yes → MEDIUM

---

## 📈 **EXPECTED IMPACT:**

### **Services That Will NOW Be Included (Previously Excluded):**
- Mental health counseling services → 50-100 resources
- Crisis helplines → 10-20 resources
- Parent/carer support groups → 30-50 resources
- Generic OT/speech therapy → 40-80 resources
- Social skills programs → 20-30 resources
- Employment support → 15-25 resources
- Respite care services → 20-30 resources

**Total Expected Increase: 185-335 additional MEDIUM-scored resources**

### **Services That Will Still Be Excluded:**
- Transport (TfL, buses) → Correctly LOW/NONE
- Councils (general authorities) → Correctly NONE
- Pharmacies, dentists → Correctly NONE
- Museums with token quiet hours → Correctly LOW

---

## ⚠️ **IMPORTANT DISTINCTIONS:**

### **✅ INCLUDE (MEDIUM):**
- Mental health clinic offering anxiety counseling
- Samaritans crisis helpline
- Parent support group for SEND children
- Occupational therapy (pediatric)
- Social skills training program
- Job coaching for people with disabilities

### **❌ EXCLUDE (LOW/NONE):**
- Transport for London
- General hospital (no ND clinic)
- Museum with occasional quiet hour
- Generic gym
- Council (general)
- Pharmacy

---

## 🚀 **NEXT STEPS:**

1. ✅ **Prompt Updated** - More inclusive criteria implemented
2. ⏳ **Test on Sample Resources** - Verify correct scoring
3. ⏳ **Run Full Re-validation** - Apply to entire dataset
4. ⏳ **Analyze Results** - Count new MEDIUM scores vs previous
5. ⏳ **User Review** - Spot-check accuracy

---

## 📝 **CHANGED FILES:**

- `src/web_llm_extract.py` (Lines 174-320)
  - Updated core question from "SPECIFICALLY DESIGNED" to "HELPS neurodivergent people"
  - Added 7 new MEDIUM categories
  - Added 5 new concrete examples
  - Updated decision framework
  - Added comprehensive recognition patterns

---

## 🎯 **ALIGNMENT WITH PROJECT GOAL:**

**Project Goal:** "Provide resource centers that help neurodivergent people"

**Old Prompt:** Too narrow - only included ND-specific services
**New Prompt:** Aligned - includes all services that help ND people and families

This revision ensures the directory is **comprehensive and useful** for the neurodivergent community, not just a list of specialist clinics.

