"""Scam-signal rule definitions for the coercion-detection engine.

Each signal belongs to one of the twelve coercion stages. Patterns cover both
English and Hindi (Devanagari plus common romanised Hindi). Weights follow the
product specification and are combined by the risk engine, which also applies
sequence bonuses, repetition dampening and normalisation.
"""
import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Signal:
    id: str
    stage: str
    label: str
    label_hi: str
    weight: float
    patterns: tuple[str, ...]
    explanation: str
    explanation_hi: str
    # Awareness guards: if one of these matches near the signal match, the text is
    # educating the user ("never share your OTP") rather than coercing them.
    negation_patterns: tuple[str, ...] = field(default=())


STAGES = [
    "lure",
    "authority_impersonation",
    "identity_misuse_claim",
    "criminal_accusation",
    "authority_escalation",
    "isolation",
    "secrecy",
    "continuous_call",
    "time_pressure",
    "threat",
    "payment_or_access_request",
    "payment_confirmation_pressure",
    "evidence_deletion",
]

STAGE_LABELS = {
    "lure": ("Prize / refund lure", "इनाम / रिफंड का लालच"),
    "authority_impersonation": ("Authority impersonation", "सरकारी अधिकारी का रूप धारण"),
    "identity_misuse_claim": ("Identity / Aadhaar misuse claim", "पहचान / आधार दुरुपयोग का दावा"),
    "criminal_accusation": ("Fake criminal accusation", "झूठा आपराधिक आरोप"),
    "authority_escalation": ("Escalation to higher authority", "उच्च अधिकारी को स्थानांतरण"),
    "isolation": ("Isolation from family/friends", "परिवार से अलगाव"),
    "secrecy": ("Secrecy demand", "गोपनीयता की मांग"),
    "continuous_call": ("Forced continuous call / video surveillance", "लगातार कॉल/वीडियो निगरानी"),
    "time_pressure": ("Urgency / time pressure", "समय का दबाव"),
    "threat": ("Threat of arrest / seizure / blocking", "गिरफ्तारी / जब्ती की धमकी"),
    "payment_or_access_request": ("Payment / OTP / remote-access request", "भुगतान / OTP / रिमोट एक्सेस की मांग"),
    "payment_confirmation_pressure": ("Payment confirmation pressure", "भुगतान पुष्टि का दबाव"),
    "evidence_deletion": ("Evidence deletion instruction", "सबूत मिटाने का निर्देश"),
}

# Guard phrases indicating awareness/education content rather than coercion.
AWARENESS_GUARDS = (
    r"\bnever\s+(share|give|tell|disclose)\b",
    r"\bdo(es)?\s*not\s+ask\s+for\b",
    r"\bwill\s+never\s+(ask|call|request)\b",
    r"\bbeware\b",
    r"\bstay\s+safe\b",
    r"\bawareness\b",
    r"\bfraudsters?\s+may\b",
    r"\breport\s+suspicious\b",
    r"कभी\s*(साझा|शेयर)\s*(न|नहीं)",
    r"कभी\s+नहीं\s+मांगत",
    r"नहीं\s+मांगत",  # "बैंक कभी OTP नहीं मांगता"
    r"सावधान\s+रह",
)

SIGNALS: tuple[Signal, ...] = (
    # Opening-stage signals come first: within a single message, first-seen stage
    # order follows this tuple, which the sequence bonuses rely on.
    Signal(
        id="prize_refund_lure",
        stage="lure",
        label="Prize / lottery / accidental-transfer refund lure",
        label_hi="इनाम / लॉटरी / गलत ट्रांसफर रिफंड का लालच",
        weight=10,
        patterns=(
            r"\b(won|winner of|selected for)\b[^.।]{0,40}\b(lottery|lucky draw|prize|reward|jackpot)\b",
            r"\b(processing|claim|registration|clearance|handling)\s+fee\b",
            r"\b(accidentally|by mistake|wrongly)\b[^.।]{0,40}\b(sent|transferred|paid)\b",
            r"\brefund\s+will\s+(process|be processed|be credited)\b",
            r"(लॉटरी|इनाम|लकी\s+ड्रॉ)[^.।]{0,40}(जीत|निकल)",
            r"(गलती\s+से)[^.।]{0,40}(भेज|ट्रांसफर)",
        ),
        explanation="An unexpected prize or 'accidental transfer' story is the lure that precedes a fee, OTP or payment demand.",
        explanation_hi="अचानक इनाम या 'गलत ट्रांसफर' की कहानी वह चारा है जिसके बाद फीस, OTP या भुगतान की मांग आती है।",
        negation_patterns=AWARENESS_GUARDS,
    ),
    Signal(
        id="authority_claim",
        stage="authority_impersonation",
        label="Caller claims to be police / CBI / ED / customs / RBI / court / telecom official",
        label_hi="कॉलर खुद को पुलिस / सीबीआई / ईडी / कस्टम / RBI अधिकारी बताता है",
        weight=8,
        patterns=(
            r"\b(i am|this is|speaking from|calling from|officer from|मैं|हम)\b[^.।]{0,60}\b(cbi|c\.b\.i|police|ed\b|enforcement directorate|customs|rbi|r\.b\.i|trai|income tax|cyber ?cell|crime branch|interpol|narcotics|ncb|court|magistrate|सीबीआई|पुलिस|प्रवर्तन निदेशालय|कस्टम|साइबर सेल|अदालत|इनकम टैक्स)",
            r"\b(cbi|police|ed|customs|rbi|trai|ncb)\s+(officer|inspector|official|department)\b",
            r"(सीबीआई|पुलिस|कस्टम)\s*(अधिकारी|इंस्पेक्टर|विभाग)",
            r"\bdigital\s+arrest\s+(unit|cell|department)\b",
            r"\b(calling|speaking)\s+from\b[^.।]{0,40}\b(bank'?s?|card)\s+(security|fraud|verification)\s+(department|team|cell|desk)\b",
            r"(बैंक)[^.।]{0,30}(सुरक्षा|फ्रॉड)\s*(विभाग|टीम)",
        ),
        explanation="Genuine agencies do not investigate over unsolicited calls. Impersonating officials is the opening move of digital-arrest scams.",
        explanation_hi="असली एजेंसियां अनजान कॉल पर जांच नहीं करतीं। अधिकारी बनना डिजिटल अरेस्ट धोखाधड़ी की पहली चाल है।",
    ),
    Signal(
        id="aadhaar_parcel_claim",
        stage="identity_misuse_claim",
        label="Claim that Aadhaar/SIM/parcel is linked to a crime",
        label_hi="आधार/सिम/पार्सल के अपराध से जुड़े होने का दावा",
        weight=8,
        patterns=(
            r"\b(aadhaar|aadhar|pan card|sim card|your (number|phone))\b[^.।]{0,80}\b(linked|used|found|misused|registered|involved)\b",
            r"\bparcel\b[^.।]{0,80}\b(drugs|illegal|contraband|passport|seized|customs|intercepted)\b",
            r"\b(illegal|suspicious)\s+parcel\b",
            r"(आधार|सिम|पार्सल)[^.।]{0,60}(जुड़|लिंक|इस्तेमाल|पकड़|अवैध|गैरकानूनी)",
            r"आपके\s+नाम\s+(पर|से)[^.।]{0,60}(पार्सल|सिम|खाता)",
        ),
        explanation="The fake 'your identity was used in a crime' hook creates fear and makes the target defensive.",
        explanation_hi="'आपकी पहचान अपराध में इस्तेमाल हुई' का झूठा दावा डर पैदा करने की चाल है।",
    ),
    Signal(
        id="criminal_allegation",
        stage="criminal_accusation",
        label="Fake accusation of money laundering / drugs / crime",
        label_hi="मनी लॉन्ड्रिंग / ड्रग्स का झूठा आरोप",
        weight=10,
        patterns=(
            r"\b(money laundering|drug trafficking|hawala|terror(ist)? financing|human trafficking)\b",
            r"\b(case|fir|complaint|warrant|arrest warrant)\b[^.।]{0,60}\b(registered|filed|issued|against you)\b",
            r"\byou (are|have been)\s+(involved|implicated|named|charged|booked)\b",
            r"(मनी\s*लॉन्ड्रिंग|हवाला|ड्रग्स|तस्करी)",
            r"(आपके\s+खिलाफ|आपके\s+विरुद्ध)[^.।]{0,60}(केस|मामला|वारंट|एफआईआर)",
        ),
        explanation="Fabricated criminal cases pressure victims into 'cooperating' before verifying anything.",
        explanation_hi="झूठे आपराधिक मामले पीड़ित पर बिना जांच किए 'सहयोग' का दबाव बनाते हैं।",
    ),
    Signal(
        id="escalation_transfer",
        stage="authority_escalation",
        label="Call transferred to a 'senior officer' or another agency",
        label_hi="कॉल 'वरिष्ठ अधिकारी' या दूसरी एजेंसी को ट्रांसफर",
        weight=6,
        patterns=(
            r"\b(transfer(ring)?|connect(ing)?|forward(ing)?)\b[^.।]{0,50}\b(call|line)\b[^.।]{0,60}\b(cbi|senior|officer|police|ed|cyber|branch|department|headquarters)\b",
            r"\b(senior|higher)\s+(officer|official|authority)\s+(will|wants to)\s+(speak|talk)\b",
            r"(कॉल|लाइन)[^.।]{0,50}(ट्रांसफर|जोड़)[^.।]{0,50}(अधिकारी|सीबीआई|पुलिस)",
            r"वरिष्ठ\s+अधिकारी\s+(से\s+)?बात",
        ),
        explanation="Staged 'transfers' between fake departments build a theatre of legitimacy.",
        explanation_hi="नकली विभागों के बीच कॉल ट्रांसफर वैधता का नाटक रचता है।",
    ),
    Signal(
        id="isolation_instruction",
        stage="isolation",
        label="Instruction to stay away from family/friends or go to a separate room",
        label_hi="परिवार/दोस्तों से दूर रहने या अलग कमरे में जाने का निर्देश",
        weight=15,
        patterns=(
            r"\b(do not|don'?t|must not)\b[^.।]{0,40}\b(tell|inform|involve|contact|call)\b[^.।]{0,40}\b(family|wife|husband|parents|children|son|daughter|friends?|relatives?|anyone)\b",
            r"\b(go to|move to|sit in|stay in)\b[^.।]{0,30}\b(separate|closed|private|alone|empty)\s*(room)?\b",
            r"\b(stay|be)\s+alone\b",
            r"(परिवार|पत्नी|पति|माता|पिता|बच्च|दोस्त|रिश्तेदार|किसी)[^.।]{0,40}(मत\s+बता|न\s+बता|नहीं\s+बता|बात\s+मत)",
            r"(अलग|बंद)\s+कमरे\s+में",
            r"अकेले\s+(रह|बैठ)",
        ),
        explanation="Cutting the victim off from family removes the people most likely to recognise the scam. This is a hallmark of psychological captivity.",
        explanation_hi="पीड़ित को परिवार से काटना उन लोगों को हटा देता है जो धोखाधड़ी पहचान सकते थे। यह मनोवैज्ञानिक कैद की पहचान है।",
    ),
    Signal(
        id="secrecy_demand",
        stage="secrecy",
        label="Demand for confidentiality / secrecy about the 'investigation'",
        label_hi="'जांच' को गुप्त रखने की मांग",
        weight=12,
        patterns=(
            r"\b(confidential|secret|classified|national security)\b[^.।]{0,60}\b(matter|case|investigation|do not|don'?t)?",
            r"\b(do not|don'?t)\s+(discuss|share|disclose|reveal|mention)\b[^.।]{0,40}\b(this|case|investigation|call)\b",
            r"\bkeep\s+(this|it)\s+(secret|confidential|between us)\b",
            r"(गुप्त|गोपनीय)\s*(रख|मामला|जांच)",
            r"किसी\s+(को|से)[^.।]{0,30}(मत|न|नहीं)\s*(बता|कह)",
        ),
        explanation="Legitimate investigations never require the subject to keep them secret from family or a lawyer.",
        explanation_hi="असली जांच में परिवार या वकील से बात करने पर कभी रोक नहीं होती।",
    ),
    Signal(
        id="continuous_call_demand",
        stage="continuous_call",
        label="Demand to stay on the call / keep video on continuously",
        label_hi="कॉल पर बने रहने / वीडियो चालू रखने की मांग",
        weight=10,
        patterns=(
            r"\b(do not|don'?t|never)\s+(disconnect|hang up|end|cut|leave)\b[^.।]{0,30}(call|video|line)?",
            r"\b(stay|remain|keep)\s+on\s+(the\s+)?(call|video|line|camera)\b",
            r"\b(keep|leave)\s+(your\s+)?(camera|video)\s+on\b",
            r"\bunder\s+(video|camera)\s+(surveillance|monitoring|observation)\b",
            r"(कॉल|वीडियो|कैमरा)[^.।]{0,40}(मत\s+काट|बंद\s+मत|चालू\s+रख|कटना\s+नहीं)",
            r"(वीडियो|कैमरे)\s+पर\s+(बने\s+रह|निगरानी)",
        ),
        explanation="Forcing an unbroken call keeps the victim under real-time control and stops them from thinking or verifying.",
        explanation_hi="लगातार कॉल पीड़ित को सोचने या पुष्टि करने से रोककर नियंत्रण में रखती है।",
    ),
    Signal(
        id="urgency_deadline",
        stage="time_pressure",
        label="Urgent deadline / immediate action demanded",
        label_hi="तुरंत कार्रवाई / समय-सीमा का दबाव",
        weight=8,
        patterns=(
            r"\b(immediately|right now|within|in the next)\b[^.।]{0,25}\b(minutes?|hours?|now)\b",
            r"\b(immediately|urgently|right away|at once)\b",
            r"\b(?<!no )hurry\b",
            r"\b(closes?|expires?)\s+in\s+\d+\s+(minutes?|hours?)\b",
            r"\blast\s+(chance|warning)\b",
            r"\bbefore\s+(midnight|tonight|the end of)\b",
            r"(तुरंत|अभी|फौरन|जल्दी)",
            r"आखिरी\s+(मौका|चेतावनी)",
            r"(घंटे|मिनट)\s+के\s+(अंदर|भीतर)",
        ),
        explanation="Artificial urgency prevents verification. Real institutions allow time and written process.",
        explanation_hi="कृत्रिम जल्दबाजी पुष्टि करने से रोकती है। असली संस्थाएं समय और लिखित प्रक्रिया देती हैं।",
    ),
    Signal(
        id="arrest_threat",
        stage="threat",
        label="Threat of arrest / digital arrest / account freeze / property seizure",
        label_hi="गिरफ्तारी / डिजिटल अरेस्ट / खाता फ्रीज की धमकी",
        weight=12,
        patterns=(
            r"\bdigital(ly)?\s+arrest(ed)?\b",
            r"\b(you )?(will|can|shall)\s+be\s+arrested\b",
            r"\barrest\s+(warrant|order)\b",
            r"\b(account|bank account)s?\s+(will\s+be\s+|would\s+be\s+)?(blocked|frozen|seized|suspended)\b",
            r"\b(property|assets?)\s+(will\s+be\s+)?(seized|attached|confiscated)\b",
            r"\b(jail|imprisonment|custody|non.?bailable)\b",
            r"\b(power|electricity|connection|service|supply|sim)\b[^.।]{0,40}\b(disconnected|cut|suspended|deactivated)\b",
            r"डिजिटल\s+अरेस्ट",
            r"गिरफ्तार(ी)?\s*(हो|कर|वारंट)?",
            r"(खाता|अकाउंट)[^.।]{0,30}(फ्रीज|ब्लॉक|सीज|बंद)",
            r"(जेल|हिरासत|संपत्ति\s+जब्त)",
        ),
        explanation="'Digital arrest' does not exist in Indian law. Arrest threats over calls are coercion, not procedure.",
        explanation_hi="भारतीय कानून में 'डिजिटल अरेस्ट' नाम की कोई चीज नहीं है। कॉल पर गिरफ्तारी की धमकी केवल डराने की चाल है।",
    ),
    Signal(
        id="remote_access_request",
        stage="payment_or_access_request",
        label="Request to install remote-access app / share screen",
        label_hi="रिमोट एक्सेस ऐप इंस्टॉल / स्क्रीन शेयर करने की मांग",
        weight=18,
        patterns=(
            r"\b(install|download|open)\b[^.।]{0,40}\b(anydesk|teamviewer|quick ?support|rustdesk|airdroid|remote|screen ?shar\w*)\b",
            r"\bshare\s+(your\s+)?screen\b",
            r"\b(give|allow|grant)\b[^.।]{0,30}\b(remote\s+)?(access|control)\b",
            r"(एनीडेस्क|टीमव्यूअर|रिमोट)[^.।]{0,40}(इंस्टॉल|डाउनलोड)",
            r"स्क्रीन\s+(शेयर|साझा)",
        ),
        explanation="Remote-access tools give the caller direct control of your device and banking apps.",
        explanation_hi="रिमोट एक्सेस ऐप कॉलर को आपके फोन और बैंकिंग ऐप्स का सीधा नियंत्रण दे देते हैं।",
        negation_patterns=AWARENESS_GUARDS,
    ),
    Signal(
        id="otp_pin_request",
        stage="payment_or_access_request",
        label="Request for OTP / PIN / CVV / password",
        label_hi="OTP / PIN / CVV / पासवर्ड की मांग",
        weight=22,
        patterns=(
            r"\b(share|tell|send|give|read( out)?|enter|provide|confirm)\b[^.।]{0,40}\b(otp|one.?time.?password|pin|cvv|passwords?|verification code)\b",
            r"\b(otp|pin|cvv)\b[^.।]{0,30}\b(share|tell|send|batao|bata)\b",
            r"(ओटीपी|पिन|सीवीवी|पासवर्ड)[^.।]{0,40}(बता|भेज|दर्ज|शेयर|साझा)",
            r"(बता|भेज|शेयर)[^.।]{0,20}(ओटीपी|पिन)",
        ),
        explanation="No bank, police force or government agency ever asks for an OTP, PIN or CVV.",
        explanation_hi="कोई भी बैंक, पुलिस या सरकारी एजेंसी कभी OTP, PIN या CVV नहीं मांगती।",
        negation_patterns=AWARENESS_GUARDS,
    ),
    Signal(
        id="payment_request",
        stage="payment_or_access_request",
        label="Request to transfer money / pay via UPI / scan QR",
        label_hi="पैसे ट्रांसफर / UPI भुगतान / QR स्कैन की मांग",
        weight=20,
        patterns=(
            r"\b(transfer|send|sent|deposit|pay|remit|move)\b[^.।]{0,50}\b(₹|rs\.?|rupees|inr|amount|money|funds?|fee|lakh|crore|\d{3,})\b",
            r"\b(scan|use)\b[^.।]{0,25}\b(qr|upi)\b",
            r"\b(upi|gpay|google pay|phonepe|paytm)\b[^.।]{0,40}\b(id|number|transfer|send|pay)\b",
            r"(पैसे|राशि|रकम|₹|रुपये?|लाख)[^.।]{0,50}(ट्रांसफर|भेज|जमा|भुगतान)",
            r"(ट्रांसफर|भेज|जमा)[^.।]{0,30}(पैसे|राशि|रुपये|₹)",
            r"(क्यूआर|यूपीआई)[^.।]{0,30}(स्कैन|भुगतान|भेज)",
        ),
        explanation="Any demand to move money during an unsolicited 'official' call is the scam's payload.",
        explanation_hi="अनजान 'सरकारी' कॉल पर पैसे भेजने की कोई भी मांग धोखाधड़ी का असली मकसद है।",
        negation_patterns=AWARENESS_GUARDS,
    ),
    Signal(
        id="safe_account_language",
        stage="payment_or_access_request",
        label="'Safe account' / 'RBI verification account' language",
        label_hi="'सेफ अकाउंट' / 'RBI सत्यापन खाता' भाषा",
        weight=25,
        patterns=(
            r"\b(safe|secure|verification|government|rbi|supervised)\s+(custody\s+)?account\b",
            r"\baccount\s+for\s+(verification|safe ?keeping|investigation)\b",
            r"\b(money|funds?|amount)\s+(will be|is)\s+(returned|refunded)\s+after\b",
            r"(सेफ|सुरक्षित|सरकारी|सत्यापन)\s+(अकाउंट|खात)",
            r"(जांच|सत्यापन)\s+के\s+(लिए|बाद)[^.।]{0,30}(खाते|अकाउंट|वापस)",
        ),
        explanation="'Safe accounts' do not exist. The RBI and police never hold citizens' money for verification.",
        explanation_hi="'सेफ अकाउंट' जैसी कोई चीज नहीं होती। RBI या पुलिस कभी सत्यापन के लिए पैसे नहीं रखती।",
        negation_patterns=AWARENESS_GUARDS,
    ),
    Signal(
        id="payment_confirmation_pressure",
        stage="payment_confirmation_pressure",
        label="Pressure to confirm/complete the payment",
        label_hi="भुगतान पूरा करने की पुष्टि का दबाव",
        weight=10,
        patterns=(
            r"\b(have you|did you)\s+(sent|transferred|paid|completed)\b",
            r"\b(confirm|show|send)\b[^.।]{0,30}\b(payment|transaction|transfer)\s*(screenshot|receipt|reference|utr)?\b",
            r"\bcomplete\s+the\s+(payment|transfer)\s+now\b",
            r"(भुगतान|ट्रांसफर|पेमेंट)[^.।]{0,30}(हो\s+गया|पूरा|कन्फर्म|स्क्रीनशॉट|रसीद)",
        ),
        explanation="Scammers chase payment confirmation to move funds through mule accounts before recall is possible.",
        explanation_hi="ठग पैसे को म्यूल खातों से आगे निकालने के लिए भुगतान की पुष्टि पर दबाव डालते हैं।",
        negation_patterns=AWARENESS_GUARDS,
    ),
    Signal(
        id="evidence_deletion",
        stage="evidence_deletion",
        label="Instruction to delete chats / call logs / messages",
        label_hi="चैट / कॉल लॉग / संदेश मिटाने का निर्देश",
        weight=15,
        patterns=(
            r"\b(delete|erase|clear|remove)\b[^.।]{0,40}\b(chat|message|call (log|history|recording)|whatsapp|conversation|screenshot|evidence)s?\b",
            r"(चैट|मैसेज|संदेश|कॉल\s+लॉग|रिकॉर्डिंग)[^.।]{0,30}(डिलीट|मिटा|हटा)",
        ),
        explanation="Telling the victim to destroy records is consciousness of guilt — evidence the caller fears scrutiny.",
        explanation_hi="रिकॉर्ड मिटाने का निर्देश दिखाता है कि कॉलर जांच से डरता है।",
    ),
    Signal(
        id="link_bait",
        stage="payment_or_access_request",
        label="Suspicious link with account-blocking / KYC pretext",
        label_hi="KYC / खाता ब्लॉक बहाने से संदिग्ध लिंक",
        weight=12,
        patterns=(
            r"\b(click|open|visit|tap)\b[^.।]{0,40}\b(link|url|http)\b",
            r"\b(update|complete|verify)\b[^.।]{0,25}\bkyc\b",
            r"https?://[^\s]{4,}",
            r"(लिंक|केवाईसी)[^.।]{0,30}(क्लिक|खोल|अपडेट)",
        ),
        explanation="Urgent KYC links harvest credentials. Banks direct customers to official apps and branches instead.",
        explanation_hi="अर्जेंट KYC लिंक आपकी बैंकिंग जानकारी चुराते हैं। बैंक आधिकारिक ऐप या शाखा में बुलाते हैं।",
        negation_patterns=AWARENESS_GUARDS,
    ),
)

# Sequence bonuses: (earlier stage, later stage, bonus, explanation).
SEQUENCE_BONUSES: tuple[tuple[str, str, float, str], ...] = (
    (
        "authority_impersonation",
        "criminal_accusation",
        6,
        "Authority impersonation followed by a criminal accusation — the classic digital-arrest opening.",
    ),
    (
        "criminal_accusation",
        "isolation",
        8,
        "An accusation followed by isolation shows deliberate psychological entrapment, not investigation.",
    ),
    (
        "isolation",
        "payment_or_access_request",
        15,
        "Isolating the victim before demanding payment is the signature of coercive fraud.",
    ),
    (
        "threat",
        "payment_or_access_request",
        20,
        "An arrest threat immediately monetised by a payment/'safe account' demand confirms extortion intent.",
    ),
    (
        "authority_impersonation",
        "payment_or_access_request",
        20,
        "OTP/remote-access/payment demands made under an official identity are the core fraud act.",
    ),
    (
        "secrecy",
        "payment_or_access_request",
        10,
        "Secrecy demanded before payment prevents the victim from consulting anyone who could stop the transfer.",
    ),
    (
        "lure",
        "payment_or_access_request",
        15,
        "A prize/refund lure followed by a fee, OTP or payment demand is the advance-fee fraud sequence.",
    ),
    (
        "payment_or_access_request",
        "payment_confirmation_pressure",
        10,
        "Chasing payment confirmation right after the demand shows intent to move funds beyond recall.",
    ),
)

SIGNALS_BY_ID = {s.id: s for s in SIGNALS}
COMPILED = {
    s.id: [re.compile(p, re.IGNORECASE) for p in s.patterns] for s in SIGNALS
}
COMPILED_GUARDS = {
    s.id: [re.compile(p, re.IGNORECASE) for p in s.negation_patterns] for s in SIGNALS
}
