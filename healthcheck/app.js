/* ============================================
   MARTECH HEALTH CHECK — APP LOGIC
   Flow: Intro → Stack → Role → Dynamic Questions → Results → Form → Custom Solution
   ============================================ */

// ============================================
// STACK OPTIONS (shown first)
// ============================================

const STACK_CATEGORIES = [
    {
        label: "CRM & Sales",
        tools: [
            { id: "hubspot",    label: "HubSpot",    icon: "🟠", category: "crm" },
            { id: "salesforce", label: "Salesforce",  icon: "☁️", category: "crm" },
            { id: "pipedrive",  label: "Pipedrive",   icon: "🟢", category: "crm" },
            { id: "zoho",       label: "Zoho CRM",    icon: "🔵", category: "crm" },
        ]
    },
    {
        label: "Email & Marketing Automation",
        tools: [
            { id: "mailchimp",      label: "Mailchimp",       icon: "🐒", category: "email" },
            { id: "klaviyo",        label: "Klaviyo",          icon: "💚", category: "email" },
            { id: "activecampaign", label: "ActiveCampaign",   icon: "⚡", category: "email" },
            { id: "brevo",          label: "Brevo",            icon: "💙", category: "email" },
        ]
    },
    {
        label: "Advertising",
        tools: [
            { id: "gads",         label: "Google Ads",   icon: "🎯", category: "ads" },
            { id: "meta_ads",     label: "Meta Ads",     icon: "📘", category: "ads" },
            { id: "linkedin_ads", label: "LinkedIn Ads",  icon: "💼", category: "ads" },
            { id: "tiktok_ads",   label: "TikTok Ads",    icon: "🎵", category: "ads" },
        ]
    },
    {
        label: "Analytics & BI",
        tools: [
            { id: "ga4",      label: "Google Analytics", icon: "📊", category: "analytics" },
            { id: "mixpanel", label: "Mixpanel",         icon: "🟣", category: "analytics" },
            { id: "hotjar",   label: "Hotjar",           icon: "🔥", category: "analytics" },
            { id: "tableau",  label: "Tableau",           icon: "📈", category: "bi" },
            { id: "looker",   label: "Looker Studio",     icon: "👀", category: "bi" },
        ]
    },
    {
        label: "SEO & Content",
        tools: [
            { id: "semrush",   label: "Semrush",    icon: "🔍", category: "seo" },
            { id: "ahrefs",    label: "Ahrefs",     icon: "🅰️", category: "seo" },
            { id: "wordpress", label: "WordPress",   icon: "📝", category: "cms" },
            { id: "webflow",   label: "Webflow",     icon: "🌊", category: "cms" },
        ]
    },
    {
        label: "Automation & Workflow",
        tools: [
            { id: "zapier", label: "Zapier", icon: "⚡", category: "automation" },
            { id: "make",   label: "Make",   icon: "🔮", category: "automation" },
            { id: "n8n",    label: "n8n",    icon: "🔧", category: "automation" },
        ]
    },
    {
        label: "Project Management",
        tools: [
            { id: "notion", label: "Notion",     icon: "📓", category: "pm" },
            { id: "asana",  label: "Asana",       icon: "🎯", category: "pm" },
            { id: "monday", label: "Monday.com",  icon: "📋", category: "pm" },
            { id: "trello", label: "Trello",      icon: "📌", category: "pm" },
        ]
    },
    {
        label: "The Spreadsheet Situation",
        tools: [
            { id: "sheets",   label: "Google Sheets", icon: "📗", category: "spreadsheet" },
            { id: "excel",    label: "Excel",          icon: "📊", category: "spreadsheet" },
            { id: "airtable", label: "Airtable",       icon: "🟡", category: "spreadsheet" },
        ]
    },
    {
        label: "Chat, Support & E-commerce",
        tools: [
            { id: "intercom", label: "Intercom",  icon: "💬", category: "support" },
            { id: "drift",    label: "Drift",      icon: "🤖", category: "chat" },
            { id: "slack",    label: "Slack",       icon: "💬", category: "comms" },
            { id: "shopify",  label: "Shopify",     icon: "🛍️", category: "ecom" },
        ]
    }
];

const STACK_OPTIONS = STACK_CATEGORIES.flatMap(cat => cat.tools);

// ============================================
// ROLES
// ============================================

const ROLES = [
    { key: "A", text: "Founder / CEO — I wear all the hats and most of them don't fit" },
    { key: "B", text: "VP / Director of Marketing — I own the strategy and the chaos" },
    { key: "C", text: "Marketing Manager — I'm in the trenches every day" },
    { key: "D", text: "Marketing Ops / RevOps — I'm the one trying to fix all this" },
    { key: "E", text: "Other — I'm here for the roast" }
];

// ============================================
// DYNAMIC QUESTION GENERATOR
// ============================================

function generateQuestions(stack) {
    const ids = stack;
    const tools = stack.map(id => STACK_OPTIONS.find(t => t.id === id)).filter(Boolean);
    const cats = [...new Set(tools.map(t => t.category))];
    const questions = [];

    const crm = tools.find(t => t.category === "crm");
    const email = tools.find(t => t.category === "email");
    const analytics = tools.find(t => t.category === "analytics" || t.category === "bi");
    const ads = tools.filter(t => t.category === "ads");
    const automation = tools.find(t => t.category === "automation");
    const spreadsheet = tools.find(t => t.category === "spreadsheet");
    const crmName = crm ? crm.label : "your CRM";
    const emailName = email ? email.label : "your email tool";
    const analyticsName = analytics ? analytics.label : "your analytics";

    // --- PILLAR 0: Data Foundation ---

    questions.push({
        pillar: "Data Foundation", pillarIndex: 0,
        text: `If your CEO asks "how many active leads do we have?" right now — how fast can you answer?`,
        options: [
            { key: "A", text: "Panic. Then 45 minutes of tab-switching.", score: 0 },
            { key: "B", text: "I'd give a number but silently pray nobody asks how I got it.", score: 1 },
            { key: "C", text: `I'd pull it from ${crmName} pretty confidently.`, score: 2 },
            { key: "D", text: "I'd spin my laptop around and show them the live dashboard.", score: 3 }
        ]
    });

    // Data governance / ownership
    questions.push({
        pillar: "Data Foundation", pillarIndex: 0,
        text: "Who owns your marketing data? Like, specifically — who's responsible for data quality, definitions, and hygiene?",
        options: [
            { key: "A", text: "Nobody. It's everyone's job, which means it's nobody's job.", score: 0 },
            { key: "B", text: "Someone sort of owns it informally but it's not their main role.", score: 1 },
            { key: "C", text: "We have a designated person but they lack the tools or authority to enforce standards.", score: 2 },
            { key: "D", text: "Clear ownership with documented standards, governance rules, and enforcement.", score: 3 }
        ]
    });

    // Conditional: CRM + Spreadsheet
    if (crm && spreadsheet) {
        questions.push({
            pillar: "Data Foundation", pillarIndex: 0,
            text: `You have ${crmName} AND ${spreadsheet.label}. When they disagree on a number — which one wins?`,
            options: [
                { key: "A", text: `${spreadsheet.label}. That's where the real data lives, honestly.`, score: 0 },
                { key: "B", text: "Depends who's asking. Different teams trust different sources.", score: 1 },
                { key: "C", text: `${crmName}, mostly — but people still keep side spreadsheets.`, score: 2 },
                { key: "D", text: `${crmName} is the undisputed source of truth. ${spreadsheet.label} is for modeling only.`, score: 3 }
            ]
        });
    } else {
        questions.push({
            pillar: "Data Foundation", pillarIndex: 0,
            text: "How often do you discover the same contact exists 3 times with 3 different email spellings?",
            options: [
                { key: "A", text: "That's not a bug, that's a feature of our CRM.", score: 0 },
                { key: "B", text: "Often enough that we've stopped being surprised.", score: 1 },
                { key: "C", text: "Sometimes — we have processes to catch it.", score: 2 },
                { key: "D", text: "Rarely — we automated that problem away.", score: 3 }
            ]
        });
    }

    // --- PILLAR 1: Stack Health ---

    // Shared definitions question
    questions.push({
        pillar: "Stack Health", pillarIndex: 1,
        text: `When your team says "conversion rate" — does everyone mean the same thing?`,
        options: [
            { key: "A", text: "Honestly, probably not. We've never defined it together.", score: 0 },
            { key: "B", text: "Loosely. Marketing means one thing, sales means another, and nobody's checked if the numbers match.", score: 1 },
            { key: "C", text: "We've aligned on key definitions but not everyone follows them consistently.", score: 2 },
            { key: "D", text: "Documented metric definitions that every team and tool uses the same way.", score: 3 }
        ]
    });

    // Conditional: CRM + Email integration
    if (crm && email) {
        questions.push({
            pillar: "Stack Health", pillarIndex: 1,
            text: `Does ${emailName} know what ${crmName} knows about your contacts? And vice versa?`,
            options: [
                { key: "A", text: "They're basically strangers who happen to share a contact list.", score: 0 },
                { key: "B", text: "We sync lists manually every now and then. It's a whole thing.", score: 1 },
                { key: "C", text: "There's a basic integration but engagement data doesn't flow back to CRM.", score: 2 },
                { key: "D", text: "Fully synced. CRM sees email engagement. Email tool uses CRM segments. Bi-directional.", score: 3 }
            ]
        });
    } else {
        questions.push({
            pillar: "Stack Health", pillarIndex: 1,
            text: `You're running ${tools.length} tools. What percentage are actually being used to their full potential?`,
            options: [
                { key: "A", text: "We're renting a Ferrari to drive to the mailbox.", score: 0 },
                { key: "B", text: "~25-50%. We use the basics and ignore the rest.", score: 1 },
                { key: "C", text: "~50-75%. Getting there.", score: 2 },
                { key: "D", text: "75%+. We actually read the documentation.", score: 3 }
            ]
        });
    }

    // Website traffic clarity
    questions.push({
        pillar: "Stack Health", pillarIndex: 1,
        text: `Does your team know — right now, without checking — your website traffic per page, visitors-to-lead conversion rate, and cost per lead by channel?`,
        options: [
            { key: "A", text: "We'd need to pull 3 different reports and even then it'd be fuzzy.", score: 0 },
            { key: "B", text: "We know total traffic. Per-page and conversion by channel? That's a research project.", score: 1 },
            { key: "C", text: "We track most of this but it's not in one place and it's not real-time.", score: 2 },
            { key: "D", text: "Yes — it's on the dashboard everyone checks. Updated automatically.", score: 3 }
        ]
    });

    // --- PILLAR 2: Reporting & Decisions ---

    questions.push({
        pillar: "Reporting & Decisions", pillarIndex: 2,
        text: "Building the monthly marketing report takes:",
        options: [
            { key: "A", text: "A blood sacrifice and an entire Tuesday.", score: 0 },
            { key: "B", text: "Several painful hours of copy-pasting from 6 different tabs.", score: 1 },
            { key: "C", text: "An hour or two — most of it is semi-automated.", score: 2 },
            { key: "D", text: "Zero time. It updates itself. I just add commentary.", score: 3 }
        ]
    });

    // Conditional: Ads → attribution
    if (ads.length > 0) {
        const adNames = ads.map(a => a.label).join(", ");
        questions.push({
            pillar: "Reporting & Decisions", pillarIndex: 2,
            text: `Can you trace a ${ads[0].label} click all the way to a closed deal in ${crmName}?`,
            options: [
                { key: "A", text: "Hahahahaha. No.", score: 0 },
                { key: "B", text: "We have vibes about which campaigns work. Strong vibes. But not math.", score: 1 },
                { key: "C", text: "For some campaigns, yes. Others are a complete black hole.", score: 2 },
                { key: "D", text: `Closed-loop attribution from ${ads[0].label} click to ${crmName} closed-won. We can show the math.`, score: 3 }
            ]
        });
    } else {
        questions.push({
            pillar: "Reporting & Decisions", pillarIndex: 2,
            text: "Can you connect a dollar of marketing spend to a dollar of revenue?",
            options: [
                { key: "A", text: "Hahahahaha. No.", score: 0 },
                { key: "B", text: "We have vibes. Strong vibes. But not math.", score: 1 },
                { key: "C", text: "For some channels, yes. Others are a black hole.", score: 2 },
                { key: "D", text: "Multi-touch attribution across most channels. We can show our work.", score: 3 }
            ]
        });
    }

    // BI / analyst support
    questions.push({
        pillar: "Reporting & Decisions", pillarIndex: 2,
        text: "Do you have a data analyst or BI resource to help make sense of your marketing data?",
        options: [
            { key: "A", text: "No. The marketing team Googles \"how to pivot table\" once a month.", score: 0 },
            { key: "B", text: "Sort of — someone on the team is \"the data person\" on top of their actual job.", score: 1 },
            { key: "C", text: "We have a shared analyst but marketing isn't their priority.", score: 2 },
            { key: "D", text: "Dedicated BI support that actually understands our marketing KPIs.", score: 3 }
        ]
    });

    // --- PILLAR 3: Automation Readiness ---

    questions.push({
        pillar: "Automation Readiness", pillarIndex: 3,
        text: "A lead fills out a form on your website. Then what?",
        options: [
            { key: "A", text: "It goes into a spreadsheet. Someone will get to it. Probably.", score: 0 },
            { key: "B", text: "They get a generic \"thanks!\" email. Then the ball's in sales' court.", score: 1 },
            { key: "C", text: "They enter an automated sequence with some personalization.", score: 2 },
            { key: "D", text: "Scored, routed, and nurtured based on who they are and what they did. Automatically.", score: 3 }
        ]
    });

    // Conditional: Has automation tool
    if (automation) {
        questions.push({
            pillar: "Automation Readiness", pillarIndex: 3,
            text: `You have ${automation.label}. How many active workflows are actually running right now?`,
            options: [
                { key: "A", text: "We set it up once. I think there's one zap that sends a Slack notification.", score: 0 },
                { key: "B", text: "A handful — basic stuff like form notifications and list syncs.", score: 1 },
                { key: "C", text: "10-20 workflows handling lead routing, data sync, and some reporting.", score: 2 },
                { key: "D", text: "It's the backbone of our ops. Multi-step workflows across marketing, sales, and data.", score: 3 }
            ]
        });
    } else {
        questions.push({
            pillar: "Automation Readiness", pillarIndex: 3,
            text: "How much of your marketing team's week is spent on tasks a robot could do?",
            options: [
                { key: "A", text: "40%+. We are the robots.", score: 0 },
                { key: "B", text: "20-40%. We know it's a problem. We're too busy to fix it.", score: 1 },
                { key: "C", text: "Some, but we've automated the most soul-crushing stuff.", score: 2 },
                { key: "D", text: "Very little. The machines do the boring parts.", score: 3 }
            ]
        });
    }

    questions.push({
        pillar: "Automation Readiness", pillarIndex: 3,
        text: "Your team's relationship with AI and automation is best described as:",
        options: [
            { key: "A", text: "\"We'll get to it after we fix the spreadsheet situation.\"", score: 0 },
            { key: "B", text: "\"We're curious but honestly don't know where to start.\"", score: 1 },
            { key: "C", text: "\"We're experimenting — a few tools here and there.\"", score: 2 },
            { key: "D", text: "\"It's embedded in our workflows and we're never going back.\"", score: 3 }
        ]
    });

    return questions;
}

// ============================================
// PILLARS & STAGES
// ============================================

const PILLARS = [
    { name: "Data Foundation", icon: "🗄️" },
    { name: "Stack Health", icon: "🔧" },
    { name: "Reporting & Decisions", icon: "📊" },
    { name: "Automation Readiness", icon: "⚡" }
];

const STAGES = [
    {
        name: "Fragmented", range: [0, 25], color: "var(--red)",
        roast: "\"It's not a tech stack. It's a tech... pile.\"",
        description: "Your leadership can't get a straight answer on pipeline or ROI without someone spending half a day in spreadsheets. Every board meeting is a fire drill. Your analysts — if you have them — are buried in data plumbing instead of finding insights.",
        detail: "The real cost isn't the tools. It's executive time wasted waiting for numbers, decisions delayed because nobody trusts the data, and analyst capacity consumed by grunt work instead of strategy. AI-powered martech eliminates this entirely — dashboards update themselves, attribution runs in real-time, leadership walks into meetings with answers."
    },
    {
        name: "Reactive", range: [26, 45], color: "var(--orange)",
        roast: "\"You have a Ferrari. You use it to check the mail.\"",
        description: "You've invested in tools but your team is firefighting data issues instead of using data for decisions. Exec asks for a number, analyst scrambles for 3 hours, number arrives too late to be useful. Your BI resource spends 70% of their time assembling reports instead of doing analysis.",
        detail: "The bottleneck isn't budget or headcount — it's that your analyst is manually connecting dots that should be automated. Fix the integration layer and your existing team gets 15+ hours/week back for strategic work."
    },
    {
        name: "Organized", range: [46, 65], color: "var(--yellow)",
        roast: "\"Not bad. Someone on your team clearly has opinions about CRM hygiene.\"",
        description: "Your foundation is solid — data has a home, core systems connect. The gap is speed and depth. Leadership shouldn't need to schedule time with BI to prep for a strategy meeting. The insights should be waiting when they sit down.",
        detail: "The opportunity now: AI that surfaces insights proactively, dashboards that answer tomorrow's questions before they're asked, and workflows that free analysts for the high-leverage work — modeling scenarios, not pulling reports."
    },
    {
        name: "Optimized", range: [66, 85], color: "var(--green)",
        roast: "\"Your reporting is automated? Can we hire your ops person?\"",
        description: "Integrated stack, trustworthy data, execs get answers without filing a ticket with BI. You're ahead of 85% of companies your size. Analysts do actual analysis instead of data janitorial work.",
        detail: "Next frontier: agentic AI that recommends actions, reallocates budget based on signals, and surfaces competitive intelligence before you ask. Your data foundation means AI can actually deliver here."
    },
    {
        name: "Autonomous", range: [86, 100], color: "var(--green)",
        roast: "\"Either you're lying or you should be selling this as a service.\"",
        description: "Your martech is a strategic advantage, not a cost center. Real-time visibility, analysts on strategy, AI on operations. If this is accurate, you're running the model most companies aspire to.",
        detail: "The risk is complacency. AI landscape evolves quarterly. What's cutting-edge today is table stakes in 18 months."
    }
];

// ============================================
// STATE
// ============================================

let generatedQuestions = [];
let currentQuestion = 0;
let answers = [];
let selectedStack = [];
let selectedRole = "";
let userData = { name: "", email: "", company: "" };

// ============================================
// NAVIGATION
// ============================================

function showScreen(id) {
    document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
    document.getElementById(id).classList.add("active");
    window.scrollTo(0, 0);
}

function startQuiz() {
    showScreen("screen-stack");
    renderStackPicker();
}

// ============================================
// STACK PICKER (STEP 1)
// ============================================

function renderStackPicker() {
    const container = document.getElementById("stack-categories");
    container.innerHTML = "";
    STACK_CATEGORIES.forEach(cat => {
        const section = document.createElement("div");
        section.className = "stack-category";
        section.innerHTML = `<div class="stack-category-label">${cat.label}</div>`;
        const grid = document.createElement("div");
        grid.className = "stack-category-grid";
        cat.tools.forEach(tool => {
            const chip = document.createElement("button");
            chip.className = "stack-chip";
            chip.dataset.id = tool.id;
            chip.innerHTML = `<span class="stack-chip-icon">${tool.icon}</span><span>${tool.label}</span><span class="stack-chip-check">✓</span>`;
            chip.addEventListener("click", () => toggleStack(tool.id, chip));
            grid.appendChild(chip);
        });
        section.appendChild(grid);
        container.appendChild(section);
    });
    updateStackCount();
}

function toggleStack(id, chip) {
    const idx = selectedStack.indexOf(id);
    if (idx > -1) { selectedStack.splice(idx, 1); chip.classList.remove("selected"); }
    else { selectedStack.push(id); chip.classList.add("selected"); }
    updateStackCount();
    document.getElementById("stack-next-btn").disabled = selectedStack.length === 0;
}

function updateStackCount() {
    const n = selectedStack.length;
    const label = document.getElementById("stack-count");
    if (n === 0) label.textContent = "Tap the tools you use";
    else if (n <= 3) label.textContent = `${n} selected — pretty lean`;
    else if (n <= 7) label.textContent = `${n} selected — solid stack`;
    else if (n <= 10) label.textContent = `${n} selected — getting crowded in here`;
    else label.textContent = `${n} selected — okay, we see the problem already`;
}

function submitStack() {
    if (selectedStack.length === 0) return;
    showScreen("screen-role");
    renderRolePicker();
}

// ============================================
// ROLE PICKER (STEP 2)
// ============================================

function renderRolePicker() {
    const container = document.getElementById("role-options");
    container.innerHTML = "";
    ROLES.forEach((role, i) => {
        const btn = document.createElement("button");
        btn.className = "option-btn";
        btn.innerHTML = `<span class="option-key">${role.key}</span><span>${role.text}</span>`;
        btn.addEventListener("click", () => {
            document.querySelectorAll("#role-options .option-btn").forEach((b, j) => b.classList.toggle("selected", j === i));
            selectedRole = role.text;
            setTimeout(() => {
                // Generate dynamic questions based on stack
                generatedQuestions = generateQuestions(selectedStack);
                currentQuestion = 0;
                answers = [];
                showScreen("screen-question");
                renderQuestion();
            }, 300);
        });
        container.appendChild(btn);
    });
}

// ============================================
// DYNAMIC QUESTIONS (STEP 3)
// ============================================

function renderQuestion() {
    const q = generatedQuestions[currentQuestion];
    const total = generatedQuestions.length;
    const container = document.querySelector("#screen-question .question-container");
    container.style.animation = "none";
    container.offsetHeight;
    container.style.animation = "fadeUp 0.35s ease";

    const step = currentQuestion + 1;
    document.getElementById("progress-fill").style.width = ((step / total) * 100) + "%";
    document.getElementById("progress-text").textContent = `${step} / ${total}`;
    document.getElementById("pillar-tag").textContent = q.pillar;
    document.getElementById("question-text").textContent = q.text;

    const optContainer = document.getElementById("options-container");
    optContainer.innerHTML = "";
    q.options.forEach((opt, i) => {
        const btn = document.createElement("button");
        btn.className = "option-btn";
        btn.innerHTML = `<span class="option-key">${opt.key}</span><span>${opt.text}</span>`;
        btn.addEventListener("click", () => selectOption(i, opt.score));
        optContainer.appendChild(btn);
    });
}

function selectOption(index, score) {
    document.querySelectorAll("#screen-question .option-btn").forEach((btn, i) => btn.classList.toggle("selected", i === index));
    answers[currentQuestion] = { questionIndex: currentQuestion, pillarIndex: generatedQuestions[currentQuestion].pillarIndex, score };

    setTimeout(() => {
        currentQuestion++;
        if (currentQuestion < generatedQuestions.length) renderQuestion();
        else showResults();
    }, 300);
}

document.addEventListener("keydown", (e) => {
    if (!document.getElementById("screen-question").classList.contains("active")) return;
    const map = { a: 0, b: 1, c: 2, d: 3 };
    const idx = map[e.key.toLowerCase()];
    if (idx !== undefined && generatedQuestions[currentQuestion]?.options[idx]) {
        selectOption(idx, generatedQuestions[currentQuestion].options[idx].score);
    }
});

// ============================================
// SCORING
// ============================================

function calculateScores() {
    const pillarScores = [0, 0, 0, 0];
    const pillarCounts = [0, 0, 0, 0];
    answers.forEach(a => { pillarScores[a.pillarIndex] += a.score; pillarCounts[a.pillarIndex]++; });
    const pillarPcts = pillarScores.map((s, i) => {
        const max = pillarCounts[i] * 3;
        return max > 0 ? Math.round((s / max) * 100) : 0;
    });
    const total = pillarScores.reduce((a, b) => a + b, 0);
    const maxTotal = answers.length * 3;
    return { pillarPcts, overallPct: Math.round((total / maxTotal) * 100) };
}

function getStage(pct) { return STAGES.find(s => pct >= s.range[0] && pct <= s.range[1]) || STAGES[0]; }

function getPillarComment(pi, pct) {
    const c = {
        0: [
            "No unified customer record. Every team works off a different version of the truth.",
            "CRM exists but data is inconsistent — duplicates, missing fields, no governance.",
            "Solid foundation. Data hygiene needs tightening but you have a source of truth.",
            "Clean, governed, unified data. Everything downstream benefits from this."
        ],
        1: [
            "Tools can't see each other. Every disconnect = manual work + data gaps + bad decisions.",
            "Partial integrations with key gaps. Data moves between some systems but handoffs break.",
            "Most systems connected. Remaining gaps cost you speed, not accuracy.",
            "Integrated stack with clean data flows. Tools amplify each other."
        ],
        2: [
            "No attribution, no automated reporting. Budget decisions are gut-based.",
            "Some reporting but it's manual and slow. Data arrives after the decision window closes.",
            "Reporting works but attribution has blind spots. You can answer most questions — slowly.",
            "Real-time dashboards and working attribution. Marketing proves ROI with confidence."
        ],
        3: [
            "Nearly everything is manual. 30-40% of team time goes to work a machine should do.",
            "Basic automation exists but complex workflows are manual. Scaling = more hiring.",
            "Core workflows automated. Next: AI-assisted ops and predictive scoring.",
            "Advanced automation with AI. Team does strategy while systems handle execution."
        ]
    };
    return c[pi][pct <= 25 ? 0 : pct <= 50 ? 1 : pct <= 75 ? 2 : 3];
}

// ============================================
// STACK DIAGNOSIS
// ============================================

function getStackDiagnosis(stack, pillarPcts) {
    const issues = [];
    const tools = stack.map(id => STACK_OPTIONS.find(t => t.id === id)).filter(Boolean);
    const cats = tools.map(t => t.category);
    const ids = stack;
    const crms = tools.filter(t => t.category === "crm");
    const emailTools = tools.filter(t => t.category === "email");

    if (crms.length > 1) issues.push(`Running ${crms.map(c => c.label).join(" AND ")}? That's a custody battle for your contact data. Pick one. Migrate. Move on.`);
    if (cats.includes("spreadsheet") && !cats.includes("crm")) issues.push("No CRM but you've got spreadsheets. That's navigating with a paper map in 2026.");
    if (cats.includes("spreadsheet") && cats.includes("crm")) issues.push(`You have a CRM AND ${tools.find(t=>t.category==="spreadsheet").label}? The CRM is crying. Let it do its job.`);
    if (!cats.includes("analytics") && !cats.includes("bi")) issues.push("No analytics or BI tool. You're making decisions based on vibes.");
    if ((ids.includes("zapier") || ids.includes("make") || ids.includes("n8n")) && pillarPcts[3] < 50) {
        const t = tools.find(t => t.category === "automation");
        issues.push(`You have ${t.label} but your automation score is low. Gym membership, only using the sauna.`);
    }
    if ((ids.includes("gads") || ids.includes("meta_ads") || ids.includes("linkedin_ads")) && pillarPcts[2] < 50) issues.push("Spending on ads but can't prove they work. That's donating to Google with extra steps.");
    if (emailTools.length > 0 && crms.length > 0 && pillarPcts[1] < 50) issues.push(`${emailTools[0].label} + ${crms[0].label} barely talking? That disconnect is costing you leads. Literally.`);
    if (stack.length > 10) issues.push(`${stack.length} tools. That's a martech city with no roads.`);
    if (!cats.includes("automation") && pillarPcts[3] < 50) issues.push("No automation tool. Your team IS the automation. And they're tired.");
    if (ids.includes("shopify") && pillarPcts[0] < 50) issues.push("Shopify has incredible data. You're just not piping it anywhere useful.");
    if (issues.length === 0) issues.push("Stack looks reasonable on paper. The question is whether these tools actually talk to each other.");
    return issues;
}

// ============================================
// CUSTOM SOLUTION — tool-specific
// ============================================

function generateSolution(stack, pillarPcts) {
    const tools = stack.map(id => STACK_OPTIONS.find(t => t.id === id)).filter(Boolean);
    const ids = stack;
    const cats = tools.map(t => t.category);
    const solutions = [];

    const crm = tools.find(t => t.category === "crm");
    const email = tools.find(t => t.category === "email");
    const ads = tools.filter(t => t.category === "ads");
    const analytics = tools.find(t => t.category === "analytics" || t.category === "bi");
    const automation = tools.find(t => t.category === "automation");
    const spreadsheet = tools.find(t => t.category === "spreadsheet");
    const crmName = crm ? crm.label : "a CRM";

    const weakest = pillarPcts.indexOf(Math.min(...pillarPcts));

    // PRIORITY 1: Worst pillar — with SPECIFIC tool references
    const p1 = {
        0: {
            title: "Fix Your Data Foundation",
            desc: crm
                ? `${crmName} should be your single source of truth but right now it's full of duplicates, missing fields, and data nobody trusts. We'd audit it, clean it, and set up governance so it stays clean.`
                : "You need a single source of truth for customer data. Right now it's scattered everywhere. Step one is choosing and properly configuring a CRM.",
            actions: [
                crm ? `Audit and deduplicate ${crmName} — merge duplicates, fill missing fields, standardize formats` : "Select and configure a CRM as your central data hub",
                "Define data ownership — who's responsible for quality, definitions, and hygiene",
                spreadsheet ? `Migrate critical data from ${spreadsheet.label} into ${crmName || "your CRM"} and enforce the rule: contacts live in CRM, not spreadsheets` : "Set up automated validation so bad data stops getting in",
                "Create documented metric definitions (what \"conversion\" means, how \"lead\" is defined) and enforce them across all tools"
            ],
            tools: [crm, spreadsheet].filter(Boolean).map(t => t.label)
        },
        1: {
            title: "Connect Your Stack",
            desc: `Your ${tools.length} tools don't know each other exist. We'd map the integration gaps and build the data bridges — starting with the ones that eliminate the most manual work.`,
            actions: [
                crm && email ? `Connect ${email.label} ↔ ${crmName}: bi-directional sync of contacts, segments, and engagement data` : "Integrate your core systems so data flows automatically",
                crm && ads.length ? `Pipe ${ads.map(a=>a.label).join(", ")} conversion data into ${crmName} for closed-loop attribution` : "Connect your ad platforms to your CRM for real attribution",
                analytics ? `Feed ${analytics.label} data into a unified dashboard so traffic, conversion, and revenue live in one place` : "Set up unified analytics across your key systems",
                "Eliminate redundant tools that duplicate data and create conflicts"
            ],
            tools: tools.slice(0, 5).map(t => t.label)
        },
        2: {
            title: "Build Reporting Executives Can Trust",
            desc: "Your team shouldn't spend hours building reports. We'd set up dashboards that update themselves and answer the questions leadership actually asks.",
            actions: [
                analytics ? `Build a live ${analytics.label} dashboard with the 5 metrics your leadership actually cares about` : "Set up a real-time marketing performance dashboard",
                ads.length && crm ? `Connect ${ads[0].label} → ${crmName} for closed-loop attribution (ad click → closed deal)` : "Implement multi-touch attribution so you can prove ROI",
                "Create automated weekly/monthly reports that generate themselves — just add commentary",
                "Define and document KPIs so everyone means the same thing when they say \"conversion rate\""
            ],
            tools: [analytics, crm, ads[0]].filter(Boolean).map(t => t.label)
        },
        3: {
            title: "Automate the Robot Work",
            desc: "Your senior team is doing work machines should handle. We'd map every manual process and build automated workflows for the highest-impact ones first.",
            actions: [
                crm ? `Build automated lead scoring and routing in ${crmName} — new leads get scored, prioritized, and assigned without human intervention` : "Implement automated lead scoring and routing",
                automation ? `Expand your ${automation.label} workflows: add data sync, reporting triggers, and multi-step nurture sequences` : "Implement a workflow automation platform (n8n, Make, or Zapier) to connect your tools",
                email && crm ? `Build behavior-triggered nurture sequences in ${email.label} based on ${crmName} data` : "Set up trigger-based email sequences based on prospect behavior",
                "Identify the 5 most time-consuming manual tasks and automate them within 30 days"
            ],
            tools: [automation, crm, email].filter(Boolean).map(t => t.label)
        }
    };

    solutions.push({ priority: 1, ...p1[weakest] });

    // PRIORITY 2: Most impactful stack-specific fix
    const crms = tools.filter(t => t.category === "crm");
    if (crms.length > 1) {
        solutions.push({
            priority: 2,
            title: `End the ${crms.map(c=>c.label).join(" / ")} Civil War`,
            desc: `Parallel CRMs = parallel realities. One has to go. We'd audit which has better data and adoption, migrate everything, and integrate properly.`,
            actions: [`Audit data quality in both ${crms[0].label} and ${crms[1].label}`, "Build migration plan for contacts, deals, and custom properties", "Set up integrations on the surviving CRM", "Decommission the other (it had a good run)"],
            tools: crms.map(t => t.label)
        });
    } else if (ads.length > 0 && pillarPcts[2] < 50) {
        solutions.push({
            priority: 2,
            title: `Stop Burning ${ads.map(a=>a.label).join(" + ")} Budget Blind`,
            desc: `You're running paid campaigns with no closed-loop attribution. Before spending another dollar, connect your ad data to ${crmName}.`,
            actions: [`Implement UTM standards across all ${ads.map(a=>a.label).join(", ")} campaigns`, `Connect ad conversion data to ${crmName} for click-to-revenue tracking`, "Build a channel ROI dashboard leadership can read in 30 seconds", "Set up automated alerts when CPA exceeds thresholds"],
            tools: ads.map(t => t.label).concat(crm ? [crm.label] : [])
        });
    } else if (!cats.includes("automation") && pillarPcts[3] < 60) {
        solutions.push({
            priority: 2,
            title: "Add the Missing Automation Layer",
            desc: "You have zero workflow automation. Before adding another marketing tool, add the tool that connects all your other tools.",
            actions: ["Evaluate n8n, Make, or Zapier based on your stack and complexity needs", "Start with 3 high-impact automations: lead routing, reporting, data sync", "Document manual processes so they can be systematically automated", "Build monitoring so you know when workflows break"],
            tools: ["n8n", "Make", "Zapier"]
        });
    } else {
        const sorted = [...pillarPcts].map((v, i) => ({v, i})).sort((a, b) => a.v - b.v);
        const second = sorted[1].i;
        if (second !== weakest) solutions.push({ priority: 2, ...p1[second] });
    }

    // PRIORITY 3: Quick win
    if (email && crm && pillarPcts[1] < 60) {
        solutions.push({ priority: 3, title: `Sync ${email.label} ↔ ${crmName} (This Afternoon)`, desc: `This native integration probably takes 2 hours to set up. Immediate ROI: no more manual list exports, engagement data flows to CRM, sales sees what emails a lead opened.`, actions: null, tools: [email.label, crm.label] });
    } else if (analytics && pillarPcts[2] < 60) {
        solutions.push({ priority: 3, title: `Build a Real ${analytics.label} Dashboard (This Week)`, desc: `Default reports are useless. Build a Looker Studio dashboard answering the 5 questions your team actually asks. 2 hours of work. Hundreds of hours saved.`, actions: null, tools: [analytics.label, "Looker Studio"] });
    } else if (spreadsheet && crm) {
        solutions.push({ priority: 3, title: `Kill the Shadow ${spreadsheet.label} (Today)`, desc: `Find every spreadsheet that duplicates ${crmName} data. Migrate it. Set the rule: contacts and deals live in CRM. Period.`, actions: null, tools: [spreadsheet.label, crm.label] });
    }

    return solutions;
}

// ============================================
// BEFORE/AFTER + IMPACT + MONDAY STORY
// ============================================

function getBeforeAfterVision(pillarPcts, overallPct, stack) {
    const before = [], after = [];
    const tools = stack.map(id => STACK_OPTIONS.find(t => t.id === id)).filter(Boolean);
    const crm = tools.find(t => t.category === "crm");
    const ads = tools.filter(t => t.category === "ads");
    const spreadsheet = tools.find(t => t.category === "spreadsheet");

    if (pillarPcts[0] <= 50) {
        before.push("\"How many leads?\" takes 45 min and 4 tabs");
        after.push("One dashboard. One number. Real-time.");
    } else {
        before.push("Analyst spends 5+ hrs/week deduping, not analyzing");
        after.push("Automated hygiene — analyst time goes to strategy");
    }
    if (pillarPcts[2] <= 50) {
        before.push("Board prep = panic session with BI to pull numbers");
        after.push("Execs walk in with answers. No prep scramble.");
    } else {
        before.push("Attribution is a black box — can't prove ROI");
        after.push("Every dollar tracked from spend to revenue");
    }
    if (pillarPcts[3] <= 50) {
        before.push("$150K talent doing $15/hr data entry and list pulls");
        after.push("AI handles ops. Humans do strategy.");
    } else {
        before.push("Scaling = hiring instead of building systems");
        after.push("Agentic workflows scale without headcount");
    }
    if (spreadsheet && crm && pillarPcts[0] <= 60) {
        before.push(`"Real data is in ${spreadsheet.label}, not ${crm.label}"`);
        after.push(`${crm.label} is the single source of truth`);
    } else if (ads.length && pillarPcts[2] <= 50) {
        before.push(`${ads[0].label} budget out. Leads in. No connection.`);
        after.push("Every ad dollar tracked to closed deal");
    } else {
        before.push(`${stack.length} tools, ${stack.length} versions of truth`);
        after.push("Integrated stack. Data flows automatically.");
    }
    return { before: before.slice(0, 4), after: after.slice(0, 4) };
}

function getImpactMetrics(pillarPcts, overallPct, stack) {
    const metrics = [];
    if (pillarPcts[2] <= 33) metrics.push({ number: "70%", label: "of analyst time wasted on data plumbing instead of strategic analysis" });
    else if (pillarPcts[2] <= 66) metrics.push({ number: "15+ hrs", label: "per week of analyst time reclaimed from manual reporting" });
    else metrics.push({ number: "5-8 hrs", label: "per week freed for strategic work" });

    if (overallPct <= 45) metrics.push({ number: "3 days → 3 min", label: "from 'exec asks' to 'exec gets a trusted answer'" });
    else if (overallPct <= 65) metrics.push({ number: "Real-time", label: "C-level visibility — no more prep crunches" });
    else metrics.push({ number: "Predictive", label: "AI surfaces insights before leadership asks" });

    if (stack.length > 5 && pillarPcts[1] <= 50) metrics.push({ number: `${stack.length} → ${Math.max(3, Math.ceil(stack.length * 0.6))}`, label: "tools needed when properly integrated" });
    else if (pillarPcts[3] <= 50) metrics.push({ number: "3-5x", label: "more output from existing team via automation" });
    else metrics.push({ number: "10x", label: "campaign velocity with AI workflows" });
    return metrics;
}

function getMondayStory(pillarPcts, overallPct) {
    if (overallPct <= 35) {
        return `<span class="time-tag">9:00 AM</span> Live dashboard shows weekend pipeline and campaign performance. No Slack to the analyst. <span class="time-tag">9:30 AM</span> Board deck is pre-populated. Your analyst spent Friday building a scenario model for Q3 instead of pulling numbers. <span class="time-tag">10:00 AM</span> VP walks into the leadership meeting with answers, not requests. Budget decisions happen in the meeting.`;
    }
    if (overallPct <= 60) {
        return `<span class="time-tag">9:00 AM</span> Dashboard loads with real-time data. VP sees weekend performance without pinging BI. <span class="time-tag">9:15 AM</span> Automated alert caught a CPA spike Sunday — paused in 30 seconds. Last month that would've burned 6 hours of analyst time to surface. <span class="time-tag">10:00 AM</span> Leadership reviews an AI-generated strategy brief. The meeting is about what to do, not what happened.`;
    }
    return `<span class="time-tag">9:00 AM</span> Optimization engine ran overnight A/B tests. Winner already getting more budget — no human needed. <span class="time-tag">9:15 AM</span> CRM auto-enriched 12 new contacts. SDR has prioritized list with talk tracks before coffee. <span class="time-tag">10:00 AM</span> CFO asks about ROI. Closed-loop attribution shows exactly which touchpoints drove last quarter's wins. Reallocation takes 15 minutes, not 15 days.`;
}

// ============================================
// SHOW RESULTS
// ============================================

function showResults() {
    showScreen("screen-results");
    const { pillarPcts, overallPct } = calculateScores();
    const stage = getStage(overallPct);

    setTimeout(() => {
        const circ = 2 * Math.PI * 54;
        const fill = document.getElementById("score-ring-fill");
        fill.style.stroke = stage.color;
        fill.style.strokeDashoffset = circ - (overallPct / 100) * circ;
    }, 100);
    animateNumber("score-value", overallPct);

    document.getElementById("stage-name").textContent = stage.name;
    document.getElementById("stage-name").style.color = stage.color;
    document.getElementById("stage-roast").textContent = stage.roast;
    document.getElementById("stage-description").textContent = stage.description;

    // Pillar cards
    const pc = document.getElementById("pillar-results");
    pc.innerHTML = "";
    PILLARS.forEach((pillar, i) => {
        const pct = pillarPcts[i];
        const col = pct <= 25 ? "var(--red)" : pct <= 50 ? "var(--orange)" : pct <= 75 ? "var(--yellow)" : "var(--green)";
        const card = document.createElement("div");
        card.className = "pillar-card";
        card.innerHTML = `<div class="pillar-card-header"><span class="pillar-card-name">${pillar.icon} ${pillar.name}</span><span class="pillar-card-score" style="color:${col}">${pct}%</span></div><div class="pillar-bar"><div class="pillar-bar-fill" id="pillar-bar-${i}" style="background:${col}"></div></div><div class="pillar-card-comment">${getPillarComment(i, pct)}</div>`;
        pc.appendChild(card);
        setTimeout(() => { document.getElementById(`pillar-bar-${i}`).style.width = pct + "%"; }, 200 + i * 100);
    });

    // Before/After + Impact
    const vision = getBeforeAfterVision(pillarPcts, overallPct, selectedStack);
    const impact = getImpactMetrics(pillarPcts, overallPct, selectedStack);
    const monday = getMondayStory(pillarPcts, overallPct);

    document.getElementById("results-detail").innerHTML = `
        <h3>Your Monday Morning: Now vs. Fixed</h3>
        <div class="before-after">
            <div class="ba-col ba-before">
                <div class="ba-label"><span class="ba-label-emoji">😩</span> Right Now</div>
                ${vision.before.map(b => `<div class="ba-item"><span class="ba-item-icon">✗</span><span>${b}</span></div>`).join("")}
            </div>
            <div class="ba-col ba-after">
                <div class="ba-label"><span class="ba-label-emoji">✨</span> After We Fix This</div>
                ${vision.after.map(a => `<div class="ba-item"><span class="ba-item-icon">✓</span><span>${a}</span></div>`).join("")}
            </div>
        </div>
        <h3>What You're Leaving on the Table</h3>
        <div class="impact-metrics">${impact.map(m => `<div class="impact-card"><span class="impact-number">${m.number}</span><span class="impact-label">${m.label}</span></div>`).join("")}</div>
        <div class="monday-story"><h4>Here's what this actually looks like...</h4><p>${monday}</p></div>
    `;

    // Stack diagnosis
    const stackIssues = getStackDiagnosis(selectedStack, pillarPcts);
    const stackLabels = selectedStack.map(id => STACK_OPTIONS.find(t => t.id === id)).filter(Boolean);
    document.getElementById("stack-diagnosis").innerHTML = `
        <h3>Your Stack, Diagnosed</h3>
        <div class="stack-tag-row">${stackLabels.map(t => `<span class="stack-tag">${t.icon} ${t.label}</span>`).join("")}</div>
        <div class="verdict-badge ${overallPct <= 25 ? 'verdict-red' : overallPct <= 45 ? 'verdict-orange' : overallPct <= 65 ? 'verdict-yellow' : 'verdict-green'}">${selectedStack.length} tools · ${overallPct <= 45 ? "mostly disconnected" : overallPct <= 65 ? "partially connected" : "reasonably connected"}</div>
        ${stackIssues.map(issue => `<p>${issue}</p>`).join("")}
    `;
}

// ============================================
// FORM → CUSTOM SOLUTION
// ============================================

function submitLead(e) {
    e.preventDefault();
    userData.name = document.getElementById("input-name").value;
    userData.email = document.getElementById("input-email").value;
    userData.company = document.getElementById("input-company").value;

    const submission = { timestamp: new Date().toISOString(), user: userData, role: selectedRole, stack: selectedStack, answers, scores: calculateScores() };
    const existing = JSON.parse(localStorage.getItem("healthcheck_submissions") || "[]");
    existing.push(submission);
    localStorage.setItem("healthcheck_submissions", JSON.stringify(existing));
    console.log("New submission:", JSON.stringify(submission, null, 2));

    document.getElementById("form-gate").style.display = "none";
    renderCustomSolution();
}

function renderCustomSolution() {
    const { pillarPcts, overallPct } = calculateScores();
    const solutions = generateSolution(selectedStack, pillarPcts);
    const el = document.getElementById("custom-solution");
    const firstName = userData.name.split(" ")[0] || "friend";

    el.style.display = "block";
    el.innerHTML = `
        <div class="solution-header"><h2>Your Custom Fix, ${firstName}</h2><p>Based on your exact stack and scores. Not a template.</p></div>
        ${solutions.map(s => `
            <div class="solution-card">
                <div class="solution-card-header"><span class="solution-card-priority priority-${s.priority}">${s.priority}</span><span class="solution-card-title">${s.title}</span></div>
                <p>${s.desc}</p>
                ${s.actions ? `<ul>${s.actions.map(a => `<li>${a}</li>`).join("")}</ul>` : ""}
                ${s.tools && s.tools.length ? `<div class="tools-involved">${s.tools.map(t => `<span class="tool-pill">${t}</span>`).join("")}</div>` : ""}
            </div>
        `).join("")}
        <div class="solution-cta">
            <h3>Want us to actually build this?</h3>
            <p>This is based on your ${selectedStack.length} tools and your specific gaps. We turn this into a 90-day implementation plan. First conversation is free. Zero pitch until you ask.</p>
            <a href="https://novastacks-ai.com/contact" target="_blank" class="btn-primary">Book a Free Strategy Session →</a>
        </div>
    `;
    el.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ============================================
// UTILITIES
// ============================================

function animateNumber(elementId, target) {
    const el = document.getElementById(elementId);
    const duration = 1500, start = performance.now();
    function update(now) {
        const p = Math.min((now - start) / duration, 1);
        el.textContent = Math.round((1 - Math.pow(1 - p, 3)) * target);
        if (p < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}
