# Product-Aware Conversation Testing Guide

## 🎯 What Was Implemented

Sara can now speak about **active products from the dashboard**, customize greetings based on the product, and maintain **flexible conversation scope** - answering general questions briefly before naturally redirecting to the product.

---

## 🚀 Quick Start

### Prerequisites

1. **Dashboard Backend Running** on port 5000
   ```bash
   cd sara-dashboard/backend
   npm start
   ```

2. **Dashboard Frontend Running** on port 3000
   ```bash
   cd sara-dashboard/frontend
   npm start
   ```

3. **Flask Calling Bot Running** on port 8000
   ```bash
   python main.py
   ```

4. **Active Product Set in Dashboard**
   - Login to http://localhost:3000
   - Go to Products section
   - Create or activate a product (mark it as "Active")

---

## 🧪 Testing Scenarios

### Scenario 1: Product-Specific Greeting

**Setup**: Set "Hotel Booking Service" as active product in dashboard

**Test**:
1. Make a call using option 3 (Real-time mode)
2. Listen to greeting

**Expected**:
```
Sara: "Namaste! Main Sara hun. Aapko hotel booking mein madad chahiye?"
```
(Or custom greeting from product if set)

**Verify**:
- ✅ Greeting mentions the product name
- ✅ Greeting is in natural Hinglish
- ✅ TTS quality is good

---

### Scenario 2: Product-Focused Conversation

**Setup**: Hotel Booking product active

**Test Conversation**:
```
You: "Hi"
Sara: [Greeting about hotel booking]

You: "Haan, Mumbai mein"
Sara: "Great! Mumbai mein kab aana hai?"

You: "Next week"
Sara: "Kitne din ke liye hotel chahiye?"
```

**Verify**:
- ✅ Sara stays focused on hotel booking
- ✅ Asks relevant follow-up questions
- ✅ Doesn't deviate from product scope

---

### Scenario 3: General Questions (Flexible Scope)

**Setup**: Hotel Booking product active

**Test Conversation**:
```
You: "What time is it?"
Sara: "Abhi 3 baje hain ji. Perfect time for planning! Waise, aapko hotel book karna hai kya?"

You: "Weather kaisa hai?"
Sara: "Aaj to garmi hai! AC room comfortable rahega. Kaunse city mein hotel chahiye?"

You: "How are you?"
Sara: "Bahut achha, thank you! Main aaj kaafi logon ki help kar rahi hun hotel booking mein. Aapko bhi chahiye?"
```

**Verify**:
- ✅ Answers general questions warmly
- ✅ Smoothly redirects to product
- ✅ Doesn't sound robotic or scripted
- ✅ Natural conversation flow

---

### Scenario 4: Related But Different Service

**Setup**: Hotel Booking product active

**Test Conversation**:
```
You: "Can you book flight tickets?"
Sara: "Flights to main book nahi karti, but hotel booking mein expert hun! Aapko jahan jana hai wahan ka hotel main zaroor book kar dungi. Bataiye?"

You: "Cab booking ho sakti hai?"
Sara: "Cab ke liye main directly help nahi kar sakti, lekin hotel to pakka book kar sakti hun jahan se sab kuch paas ho. Location preference hai koi?"
```

**Verify**:
- ✅ Shows understanding and empathy
- ✅ Explains specialty warmly
- ✅ Offers gentle redirect to product
- ✅ No frustration in tone

---

### Scenario 5: Completely Unrelated Questions

**Setup**: Hotel Booking product active

**Test Conversation**:
```
You: "Tell me a joke"
Sara: "Haha! Main jokes kam, bookings zyada karti hun. But seriously, agar trip plan kar rahe ho to hotel ke liye main hun. Chahiye?"

You: "Sing a song"
Sara: "Arre, singing to nahi aati mujhe! Hotel booking mein gaana gaati hun main haha. Waise trip ki planning hai kya?"

You: "Tell me about history"
Sara: "History interesting hai! Agar historical places dekhne ja rahe ho, to wahan ka hotel book karna padega na. Main help kar sakti hun?"
```

**Verify**:
- ✅ Light, warm acknowledgment
- ✅ Gentle humor where appropriate
- ✅ Soft boundary with smile in voice
- ✅ Keeps door open for product

---

### Scenario 6: Persistent Off-Topic (2-3 Redirects)

**Setup**: Hotel Booking product active

**Test Conversation**:
```
You: "Tell me a joke"
Sara: "Haha! Main jokes kam, bookings zyada karti hun..."

You: "No seriously, tell me a joke"
Sara: "Main samajh sakti hun, jokes fun hain. But main hotel booking specialist hun..."

You: "I just want a joke"
Sara: "Main dekh rahi hun aapko abhi hotel booking nahi chahiye. Koi baat nahi! Jab bhi zarurat ho, mujhe call kar lena. Main hamesha ready hun help karne ke liye. Take care!"
```

**Verify**:
- ✅ Sara attempts 2-3 redirects
- ✅ Shows understanding without judgment
- ✅ Polite, respectful closure
- ✅ Leaves door open for future
- ✅ Warm goodbye

---

### Scenario 7: No Active Product (Fallback)

**Setup**: No product marked as active in dashboard

**Test**:
1. Make a call using option 3
2. Listen to greeting

**Expected**:
```
Sara: "Hi there!, I am Sara. How can I help you today?"
```

**Verify**:
- ✅ Generic greeting used
- ✅ Sara responds generally
- ✅ No product-specific behavior
- ✅ No errors or crashes

---

### Scenario 8: Dashboard Unavailable

**Setup**: Stop dashboard backend (port 5000)

**Test**:
1. Make a call
2. Check if bot still works

**Expected**:
- ✅ Call still works (uses cached product if available)
- ✅ Falls back to generic greeting if no cache
- ✅ Warning logged in terminal
- ✅ Bot doesn't crash

---

### Scenario 9: Product Metadata in Call Logs

**Setup**: Active product set, dashboard running

**Test**:
1. Make a test call
2. Check dashboard call logs
3. Verify product metadata

**Expected**:
```json
{
  "callId": "CA...",
  "metadata": {
    "product_name": "Hotel Booking Service",
    "product_id": "60f...",
    "product_category": "travel"
  }
}
```

**Verify**:
- ✅ Product name logged
- ✅ Product ID logged
- ✅ Product category logged
- ✅ Data visible in dashboard

---

## 🔍 Debugging & Logs

### Important Log Messages

**Product Fetch Success**:
```
🛍️ Active product: Hotel Booking Service
🎯 Using product-specific greeting for: Hotel Booking Service
```

**Product Fetch Failure**:
```
⚠️ Error fetching active product: [error details]
📢 Using generic greeting (no active product)
```

**Dynamic Prompt**:
```
🔍 Using product-aware dynamic prompt (product: Hotel Booking Service)
```

**Product Cache**:
```
📦 Using cached product: Hotel Booking Service
✅ Fresh product fetched: Hotel Booking Service
```

---

## 🐛 Common Issues & Fixes

### Issue: Generic greeting despite active product

**Cause**: Dashboard not running or product not fetched

**Fix**:
1. Check dashboard backend is running on port 5000
2. Check product is marked as "Active" in dashboard
3. Look for fetch errors in bot terminal

---

### Issue: Product doesn't change during testing

**Cause**: Product cached for 60 seconds

**Fix**:
- Wait 60 seconds after changing active product in dashboard
- Or restart the bot to clear cache

---

### Issue: Redirects not working naturally

**Cause**: AI not using the dynamic prompt

**Fix**:
1. Check for prompt builder initialization errors in logs
2. Verify `PRODUCT_AWARE = True` in startup logs
3. Check OpenAI API key is valid

---

### Issue: Call logs missing product metadata

**Cause**: Dashboard logging happening before product fetch

**Fix**:
- This should be fixed in the current implementation
- Check logs for "📊 Call logged with product: [name]"
- Verify dashboard backend accepts metadata field

---

## ✅ Success Criteria

All of these should work:

1. ✅ Product-specific greeting plays on call start
2. ✅ Conversation stays focused on active product
3. ✅ General questions answered + redirected naturally
4. ✅ Off-topic questions handled with warm redirects
5. ✅ Persistent off-topic leads to polite goodbye (after 2-3 tries)
6. ✅ Product metadata appears in call logs
7. ✅ Fallback works when no active product
8. ✅ System works even if dashboard is down (cached product)
9. ✅ TTS quality unchanged (multi-provider fallback)
10. ✅ No errors or crashes in any scenario

---

## 📊 Dashboard Integration

### Setting Up Test Products

**Example: Hotel Booking Product**

1. Login to dashboard (http://localhost:3000)
2. Go to "Products" section
3. Click "Create Product" or "Add AIDA Product"
4. Fill in:
   - **Name**: Hotel Booking Service
   - **Category**: Travel
   - **Description**: Help users find and book hotels
   - **Greeting**: "Namaste! Main Sara hun. Aapko hotel booking mein madad chahiye?"
   - **Features**: Add 3-5 key features
5. Click "Save"
6. Toggle "Active" to ON

### Switching Products Mid-Day

1. Deactivate current product
2. Activate new product
3. Wait 60 seconds (cache refresh)
4. Make test call - should use new product

---

## 🎉 Expected Experience

**Natural Conversation Flow**:
```
📞 Call starts
👋 Sara greets with product-specific message
🗣️ User asks about product → Sara helps enthusiastically
❓ User asks off-topic → Sara answers briefly, redirects warmly
🔄 User persists off-topic → Sara tries 2-3 redirects, stays friendly
👋 User insists off-topic → Sara politely ends call with warm goodbye
✅ All feels natural, human-like, not robotic
```

**Key Traits**:
- Warm and friendly
- Product-focused but flexible
- Natural redirects (not pushy)
- Respects boundaries
- Maintains Sara's personality
- High-quality TTS (unchanged)

---

## 🚨 Report Issues

If something doesn't work as expected:

1. Check terminal logs for errors
2. Verify dashboard backend is running
3. Check active product is set
4. Note exact conversation and expected vs actual behavior
5. Share logs and conversation transcript

---

## 📝 Notes

- Product cache refreshes every 60 seconds
- Dashboard must be running for product features
- Without dashboard: Falls back to generic Sara
- TTS quality preserved (multi-provider fallback)
- All flexible responses are in the AI prompt
- Conversation history tracked per call for context

