# CogniSync — Product Requirements Document

**Version:** 1.1  
**Status:** Revised planning baseline — ready for technical design and implementation planning  
**Project type:** Personalised student learning, study-effectiveness prediction and study-time recommendation prototype  
**Document date:** 12 November 2026

---

## Document control

### Revision summary

This revision consolidates the original CogniSync PRD with the subsequently agreed product decisions, the uploaded project overview and feature specification, and the team's dataset assessment.

Key decisions incorporated in v1.2:

- Preserve CogniSync's original primary purpose: recommend suitable study windows and estimate likely study effectiveness / quiz performance at a proposed study time.
- Predict **both the next quiz score and delayed topic-retention score**.
- Use OULAD as an **offline benchmark dataset**, not as a source of CogniSync user records and not automatically as the deployed model.
- Collect CogniSync's own linked study-session, quiz-attempt and delayed-quiz data for the context-aware and personalised models.
- Include a textbook meaning-preservation checker as a separate AI feature.
- Use the uploaded Newsela and WikiLarge simplification examples as supporting material for simplification evaluation, not as a substitute for factual-entailment labels.
- Do not use the uploaded SciQ-style Parquet dataset.
- Do not use the Student Lifestyle Dataset as the primary score-prediction dataset.
- Remove stress and mood completely. They are not product inputs, database fields, model features, dashboard elements or logging prompts.
- Do not require daily manual lifestyle logging.
- Keep Google Health API as the preferred consented source for supported sleep and activity data, subject to a technical proof of concept and current Google requirements.
- Keep Android-only automatic home-to-college commute tracking, with Google Maps Routes API expected-duration comparison.
- Add a dedicated Academic Workload Estimation Engine to convert the student's timetable and academic calendar into daily and future workload features.
- No iOS / Apple Health / HealthKit support in this project scope.
- No mandatory smartwatch; the application must remain useful without one.

### Product definition

CogniSync is a student-focused learning support system that combines quiz history, study behaviour, consented sleep and activity signals, academic workload and commute context to estimate likely assessment performance and recommend useful study windows. It also provides PDF-based study material ingestion, summarisation, quiz generation and a source-grounded meaning-preservation checker.

CogniSync is a prototype and research system. Predictions are estimates based on observational data; they are not causal guarantees, medical assessments or promises of academic results.

---

# 1. Executive summary

CogniSync addresses two connected student problems:

1. Students do not know which available time windows may be most suitable for effective study.
2. Students have limited ability to estimate how well they may perform on an upcoming quiz or how much of a topic they may retain after a delay.

The system will build a continuously updated representation of each student's learning and study context. It will use previous quiz outcomes and, as data becomes available, contextual features such as study timing and duration, sleep, physical activity, academic workload and commute duration.

The product has four principal capability groups:

1. **Prediction and recommendation**
   - Predict the next quiz score for a subject/topic.
   - Predict a delayed retention score for a previously studied topic.
   - Compare candidate study windows and recommend those with higher predicted effectiveness, subject to timetable, deadline and commute constraints.
   - Show uncertainty and data coverage, rather than presenting every estimate as certain.

2. **Student context**
   - Import sleep and activity data from a consented Google Health API connection, where supported.
   - Import weekly timetable and academic calendar information from student-provided PDFs.
   - Calculate daily and upcoming academic workload.
   - Track opted-in home-to-college commute duration on Android and compare it with Google Maps expected travel duration.
   - Observe study activity inside CogniSync and let students confirm or correct candidate study sessions.

3. **Study workspace**
   - Upload and process study PDFs.
   - Summarise uploaded material with source grounding and page references where available.
   - Generate topic-based quizzes from the student's own material.
   - Store quiz attempts, scores, topic, difficulty and timestamps.

4. **Meaning-preservation research feature**
   - Compare AI-simplified textbook explanations with their source passages.
   - Identify claims that appear supported, contradicted or insufficiently supported.
   - Run targeted checks for numbers, units, negation, conditions and technical terms.
   - Present flags as advisory, not as a guarantee of correctness.

The most important ML research contribution is a controlled comparison between a previous-scores-only predictor and a context-aware predictor. OULAD provides an offline benchmark for next-assessment score prediction. The deployed CogniSync models must ultimately be trained and evaluated on consented CogniSync data that links student context to actual quiz outcomes.

---

# 2. Background and project context

## 2.1 Existing project as reference

The earlier CogniSync implementation and repository are references for useful capabilities, not a codebase that the new application must extend. The redesigned project is to be developed from scratch.

Useful prior capabilities to preserve or redesign include:

- Student authentication and profiles.
- Study and learning history.
- Retention / performance prediction.
- Study-window recommendation.
- What-if study-time simulation.
- Explainability for predictions.
- PDF upload and document ingestion.
- Retrieval-augmented generation (RAG).
- AI quiz generation.
- Per-student model calibration.

The new architecture should be modular, testable and privacy-conscious rather than reproducing the old implementation structure.

## 2.2 Agreed product direction

The primary objective remains the same: help a student identify useful study windows and estimate likely study effectiveness. The project expands the data used to make those estimates; it does not replace the original objective.

The system must distinguish:

- Actual measured or externally supplied data.
- Events observed inside CogniSync.
- Student-confirmed or student-corrected information.
- Values calculated by deterministic business logic.
- Model-generated estimates and predictions.

These categories must remain distinguishable in storage, model features, explanations and the user interface.

---

# 3. Product goals

## 3.1 Primary goals

1. Predict a student's next quiz score for a given subject/topic using only information available before that quiz.
2. Predict delayed retention using a later quiz on the same topic after a defined retention interval.
3. Recommend suitable study windows by considering predicted effectiveness and actual availability.
4. Use prior scores as the baseline and evaluate whether contextual features improve predictive accuracy.
5. Adapt predictions to individual students as their own data accumulates.
6. Estimate academic workload from the student's timetable, exams, deadlines and other academic commitments.
7. Incorporate consented sleep and activity signals when available.
8. Incorporate commute context when the student opts into Android commute tracking.
9. Provide grounded summaries and quizzes from the student's own uploaded material.
10. Check whether simplified explanations preserve important meaning from source material.

## 3.2 Secondary goals

- Explain which input categories influenced a prediction.
- Show data freshness, missingness and confidence limitations.
- Let students correct timetable events, calendar events and study-session detections.
- Provide a what-if simulator for comparing candidate study times.
- Build a versioned dataset and model-evaluation process suitable for a student research project.

## 3.3 Success criteria

The product is successful if it can:

- Produce a defensible score-only baseline using OULAD.
- Record CogniSync quiz attempts and connect them to preceding study/context records.
- Train and evaluate a context-aware next-quiz predictor when sufficient CogniSync data exists.
- Collect delayed quiz outcomes for retention modelling.
- Generate workload features from confirmed timetable/calendar data.
- Recommend only genuinely available time windows.
- Make predictions with clear uncertainty and limitations.
- Evaluate the meaning checker against a human-labelled set.

No improvement in academic performance is to be claimed unless supported by an appropriately designed evaluation.

---

# 4. Non-goals and explicit exclusions

The following are explicitly outside the project scope:

- Stress tracking, stress prediction or stress-level inputs.
- Mood tracking, mood prediction or mood-level inputs.
- Any stress or mood fields in new database schemas, model feature sets, UI, prompts or manual logging.
- Medical, clinical or diagnostic fatigue assessment.
- Medical recommendations or health advice.
- Mandatory daily manual logging of sleep, activity, mood, stress or energy.
- Mandatory smartwatch ownership.
- iOS, Apple Health, HealthKit or Apple Watch integration.
- Continuous raw GPS route-history collection.
- Tracking arbitrary journeys or a student's general location history.
- Inferring offline study activity without a supported device/app integration.
- Training a foundation language model from scratch.
- Training a custom PDF OCR model from scratch.
- Training a custom routing/traffic model as part of the initial release.
- Using the uploaded SciQ-style Parquet files.
- Using static GPA/CGPA as a substitute for repeated quiz scores or measured delayed retention.
- Claiming that a recommended time causes a better score based solely on observational predictions.

A student must be able to use core study tools, quiz history and timetable-based recommendations without connecting a wearable or enabling commute tracking.

---

# 5. Target users and use cases

## 5.1 Primary user

A university or college student who wants to plan study time, monitor topic-level quiz performance and understand how their recent routine and academic commitments relate to study outcomes.

## 5.2 Core use cases

1. A student uploads their weekly timetable and academic calendar.
2. A student connects a supported Google Health data source with explicit consent.
3. A student optionally enables Android home-to-college commute detection.
4. A student uploads a textbook or lecture PDF.
5. CogniSync summarises a selected topic and generates a quiz.
6. CogniSync records the quiz result and associates it with relevant preceding study sessions.
7. CogniSync predicts the student's next quiz score for that topic.
8. CogniSync schedules or presents a delayed retention quiz.
9. CogniSync estimates workload for today and upcoming days.
10. CogniSync compares free study windows and recommends suitable candidates.
11. A student reviews, corrects or dismisses a detected in-app study session.
12. A student disconnects an integration and requests data deletion/export.

---

# 6. Functional requirements

## 6.1 Authentication and student profile

- **FR-AUTH-01:** Students shall be able to register, sign in, sign out and securely manage their accounts.
- **FR-AUTH-02:** Each student's records shall be associated with a pseudonymous internal student identifier.
- **FR-AUTH-03:** Students shall be able to set timezone, institution/semester details and relevant academic preferences.
- **FR-AUTH-04:** Students shall be able to export and request deletion of their personal data.
- **FR-AUTH-05:** The application shall not require health integration or commute tracking to create an account or use core study features.

## 6.2 Google Health API integration

### Purpose

Retrieve supported sleep and physical activity records from a student's Google Health account after explicit OAuth consent.

### Preferred integration

Use Google's Health API directly through a server-side OAuth 2.0 integration, subject to a technical proof of concept and current API eligibility, scopes, terms and pricing verification.

This is distinct from implementing a native Health Connect reader. The chosen direct API approach must be validated against real user accounts and real source devices before it is treated as a supported production integration.

### Required data, where available and authorised

- Sleep start and end timestamps.
- Sleep duration.
- Sleep timing and regularity features derived from available records.
- Steps.
- Activity / exercise duration.
- Active minutes or equivalent activity summaries, if exposed.
- Activity intensity/type, if exposed.
- Heart rate and sleep-stage information only if available, necessary and covered by granted scopes.

The application must not assume that every smartwatch brand or fitness app exposes every data type through Google Health. A source compatibility matrix must be established during technical validation.

### Functional requirements

- **FR-HEALTH-01:** Explain the purpose of each requested data category before OAuth consent.
- **FR-HEALTH-02:** Request only the minimum scopes required for selected features.
- **FR-HEALTH-03:** Keep OAuth client secrets and refresh/access tokens server-side; never expose them to browser JavaScript.
- **FR-HEALTH-04:** Store source provenance, source timestamps, sync timestamps and data quality indicators.
- **FR-HEALTH-05:** Support incremental synchronisation where the API permits.
- **FR-HEALTH-06:** Handle missing records, duplicate records, token expiry, consent revocation and API errors.
- **FR-HEALTH-07:** Show connection state and last successful sync.
- **FR-HEALTH-08:** Allow the student to disconnect the integration and delete locally stored imported records as required by the retention policy.
- **FR-HEALTH-09:** Do not infer that missing data means zero sleep or zero activity.
- **FR-HEALTH-10:** The application shall remain usable when no health source is connected.

### Google API setup and release constraints

A developer-owned Google Cloud project and OAuth client configuration are expected to be required. Students should only need to sign in with their own Google accounts and grant consent; they should not need to create cloud projects.

Before release, verify current requirements for:

- API access and account eligibility.
- OAuth consent-screen configuration.
- Testing-mode user limits and token expiry behaviour.
- Verification requirements for wider distribution.
- Permitted scopes and data-use restrictions.
- Any applicable Cloud/API charges or security assessment requirements.

Do not assume that the API is permanently free, that testing-mode refresh tokens never expire, or that every wearable source is supported. Do not enable the separate Google Cloud Healthcare API as a substitute for the intended Google Health API integration.

## 6.3 Academic timetable and calendar ingestion

### Purpose

Convert student-uploaded weekly timetable and academic-calendar PDFs into confirmed structured schedule records.

### Inputs

- Weekly class timetable.
- Academic calendar containing internals, semester examinations, assignments, project submissions, holidays and other academic events.
- Optional student corrections or manually added academic commitments.

### Processing

- Use PyMuPDF for text-based PDFs.
- Use OCR for scanned/image-only pages.
- Use AI-assisted extraction/normalisation to identify event names, dates, times, subjects, event types and relevant metadata.
- Detect ambiguous dates, missing times, conflicting events and uncertain extraction.
- Present extracted records for student confirmation or correction before they influence recommendations.
- Preserve original source document and page references where feasible.

### Functional requirements

- **FR-CAL-01:** Support timetable and academic-calendar PDF upload.
- **FR-CAL-02:** Extract recurring weekly classes and one-off academic events.
- **FR-CAL-03:** Support event categories such as class, internal assessment, semester examination, assignment deadline, project deadline, holiday and other academic event.
- **FR-CAL-04:** Show extracted records in a review screen.
- **FR-CAL-05:** Require confirmation or correction before uncertain extracted events are used in workload calculation.
- **FR-CAL-06:** Allow edits, additions, deletions and replacement of uploaded schedules.
- **FR-CAL-07:** Handle academic term boundaries, recurring events, date ranges and timezone.
- **FR-CAL-08:** Detect timetable/calendar conflicts and duplicate events.
- **FR-CAL-09:** Keep extraction confidence and student-confirmation status.
- **FR-CAL-10:** Recalculate future workload and study availability after confirmed schedule changes.

PDF extraction is an ingestion capability. It is not a custom ML training objective for this project.

## 6.4 Academic Workload Estimation Engine

### Purpose

Calculate how academically occupied or demanding a day and upcoming period appear from confirmed timetable and calendar records. This engine is essential because the prediction model must receive numerical workload features rather than raw PDF documents or vague labels such as "busy day".

### Inputs

- Confirmed class timetable.
- Confirmed internal and semester examination dates.
- Assignment and project deadlines.
- Other confirmed academic events.
- Optional student-entered task effort, progress and pending-work information.
- Student-confirmed study sessions, where relevant to workload/backlog features.

### Derived features

At minimum, calculate:

- `class_hours_day`
- `class_count_day`
- `scheduled_free_hours_day`
- `exam_count_next_7d`
- `exam_count_next_14d`
- `days_to_next_exam`
- `deadline_count_next_7d`
- `deadline_count_next_14d`
- `days_to_nearest_deadline`
- `assignment_deadline_load`
- `project_deadline_load`
- `academic_event_count_day`
- `academic_event_load_next_7d`
- `academic_event_load_next_14d`
- `confirmed_pending_task_count`, if the student supplies tasks
- `estimated_pending_effort_hours`, only where supplied or otherwise explicitly estimated with provenance.

The engine should calculate both day-level and time-window-level context. An event that is imminent should influence the current workload more than a distant event. The exact urgency curve and event weights must be configurable and validated rather than treated as scientific truths.

### Workload score

The first implementation shall use a transparent deterministic scoring/ranking method, not a separately trained ML model.

A normalised daily workload score may combine:

- Scheduled class load.
- Exam proximity and assessment density.
- Assignment/project deadline proximity and count.
- Confirmed pending-work information, if available.

The PRD does not prescribe fixed weights as validated facts. Initial weights and score bands must be documented as design parameters, tested with pilot feedback and adjusted using evidence.

### Functional requirements

- **FR-WORK-01:** Calculate workload for today, tomorrow and future dates.
- **FR-WORK-02:** Calculate a rolling 7-day and 14-day workload outlook.
- **FR-WORK-03:** Distinguish confirmed schedule data from unconfirmed or inferred task information.
- **FR-WORK-04:** Explain the main contributors to a high workload score.
- **FR-WORK-05:** Recalculate scores when an event is added, moved, completed or deleted.
- **FR-WORK-06:** Do not assume that high workload necessarily means low study effectiveness.
- **FR-WORK-07:** Provide numerical workload features to the context-aware score model and recommendation engine.
- **FR-WORK-08:** Avoid double-counting overlapping academic events.
- **FR-WORK-09:** Allow the student to correct inaccurate event duration, event type or deadline.
- **FR-WORK-10:** Show missing/uncertain academic information so recommendations do not imply complete schedule knowledge.

### Important distinction

The timetable and calendar describe scheduled workload. They do not reveal the actual effort required for every assignment or project. Actual task effort and backlog can only be improved by optional student input or supported progress information. CogniSync must not pretend to know the full workload from a calendar alone.

## 6.5 Android commute tracking and Google Maps

### Purpose

Use opt-in location-based detection to estimate the duration of the student's home-to-college and college-to-home commutes, and compare actual trip duration with an expected Google Maps route duration.

### Scope

- Android only.
- Student explicitly defines home and college locations.
- Detect only the configured home/college commute use case.
- No continuous raw GPS route history.
- No general-purpose location tracking.
- Student can pause, disable, correct or delete commute records.

### Architecture

A browser-based Flask web application cannot reliably perform background geofence transitions by itself. Automatic background detection therefore requires an Android companion component (native Android app or appropriately engineered Android module) connected to the main CogniSync backend.

The Android component shall:
- Request location/background permissions only after explaining why they are needed.
- Register the minimum geofences needed for home and college.
- Detect likely departure and arrival transitions.
- Record event timestamps and confidence.
- Send derived trip events to the backend.
- Avoid uploading continuous raw GPS traces.
- Handle permission denial, battery restrictions, offline operation and duplicate transitions.

### Google Maps comparison

Use Google Maps Routes API (or the current appropriate Google routing endpoint) to obtain expected route duration for the relevant origin, destination and departure-time context.

Store:
- Expected route duration.
- Actual detected trip duration.
- Departure time and arrival time.
- Direction (home-to-college or college-to-home).
- Route/API response metadata needed for audit and refresh.
- Derived difference: `actual_duration - expected_duration`.
- Data confidence and whether the trip was student-corrected.

The expected duration must be described as a route estimate, not a guaranteed travel time. The comparison must account for direction and departure-time context where the API supports it.

### Functional requirements

- **FR-COM-01:** Commute tracking is opt-in and off by default.
- **FR-COM-02:** Student can set and edit home and college locations.
- **FR-COM-03:** Detect likely configured home-college trips on Android.
- **FR-COM-04:** Compare detected duration with Google Maps expected duration.
- **FR-COM-05:** Store derived trip information, not continuous route history.
- **FR-COM-06:** Student can correct or delete an incorrectly detected trip.
- **FR-COM-07:** Student can pause or permanently disable tracking.
- **FR-COM-08:** Handle missing permissions, GPS errors, battery optimisation and network outages gracefully.
- **FR-COM-09:** Do not invent a commute when a geofence transition is missing or ambiguous.
- **FR-COM-10:** Expose commute duration and commute deviation as optional model features only when data quality is adequate.
- **FR-COM-11:** Set API quotas, billing alerts and usage caps for Maps services.
- **FR-COM-12:** Core CogniSync functionality shall work without commute tracking.

### ML role

No custom commute-duration or traffic model is required for the initial release. Google Maps supplies the expected duration; Android supplies detected trip timestamps; CogniSync calculates the difference. Historical personal commute correction can be explored later only if sufficient reliable data exists.

## 6.6 Study workspace and PDF material

### PDF ingestion

- Students can upload study material in supported PDF formats.
- Extract text using PyMuPDF.
- Apply OCR to scanned pages where needed.
- Preserve page boundaries and source metadata.
- Chunk extracted content for retrieval.
- Generate embeddings using an existing embedding model.
- Store embeddings and document metadata in a vector store such as ChromaDB or another selected compatible store.
- Allow document deletion and re-indexing.

### Summarisation

- Summaries must be grounded in retrieved source passages.
- Include page references or source citations when available.
- Distinguish source content from generated explanation.
- Avoid unsupported facts and fabricated citations.
- Allow the student to choose a document/topic or section.
- Provide a clear indication when source extraction is poor or incomplete.

### Quiz generation

- Generate topic-based quizzes from the student's uploaded material using RAG.
- Support configurable question count and difficulty.
- Store question, answer key, source passage/page, topic, difficulty and generation metadata.
- Provide feedback and explanations grounded in source material.
- Store each attempt with timestamp, score, question-level correctness and relevant session links.
- Avoid using the excluded SciQ-style Parquet dataset in the product's model-training plan.

### Functional requirements

- **FR-STUDY-01:** Upload, list, open and delete study PDFs.
- **FR-STUDY-02:** Extract text and apply OCR where required.
- **FR-STUDY-03:** Index source content for retrieval.
- **FR-STUDY-04:** Generate grounded summaries.
- **FR-STUDY-05:** Generate quizzes from the student's own uploaded materials.
- **FR-STUDY-06:** Store quiz attempts and objective scores.
- **FR-STUDY-07:** Link quiz attempts to subject/topic and, where possible, preceding study sessions.
- **FR-STUDY-08:** Retain source references for generated questions and summaries.
- **FR-STUDY-09:** Allow students to report incorrect summaries/questions.
- **FR-STUDY-10:** Clearly separate immediate quiz performance from delayed retention measurement.

## 6.7 In-app study activity capture and session confirmation

### Purpose

Capture study activity that occurs inside CogniSync without requiring students to log every session manually.

### Observable events

Examples include:
- Open/view a PDF.
- Navigate between pages or sections.
- Request a summary.
- Start a quiz.
- Submit a quiz.
- Interact with study material.
- Start or stop an explicit study timer, if provided.

### Sessionisation

- Group related events using timestamps, app activity and inactivity thresholds.
- Use browser visibility/focus signals where supported.
- Do not count an inactive open browser tab as active study.
- Store raw observed events separately from estimated active duration.
- Derive candidate study sessions with start/end times and estimated active duration.

### Confirmation

After a grouped candidate session, show a small confirmation prompt rather than interrupting after every event. Ask whether it was a real study session and which subject/topic it related to. Allow correction of duration, confirmation, dismissal or deletion.

Optional session feedback may include perceived focus or difficulty if approved in the final UI design. It must not include mood or stress.

### Functional requirements

- **FR-SESSION-01:** Record relevant in-app study events with timestamps.
- **FR-SESSION-02:** Derive candidate sessions using configurable sessionisation logic.
- **FR-SESSION-03:** Use activity/visibility signals where available to reduce idle-time inflation.
- **FR-SESSION-04:** Distinguish observed events, estimated active time and student-confirmed sessions.
- **FR-SESSION-05:** Prompt for confirmation after a grouped session, not after every event.
- **FR-SESSION-06:** Allow subject/topic assignment and duration correction.
- **FR-SESSION-07:** Allow dismissal and deletion.
- **FR-SESSION-08:** Do not claim to track offline or external-app study without an actual supported integration.
- **FR-SESSION-09:** No mandatory daily session logging.

## 6.8 Next-quiz score prediction

### Purpose

Predict the score a student is likely to achieve on their next quiz for a particular subject/topic using information available before the quiz.

### Target

`next_quiz_score`, represented on a consistent 0–100 scale or normalised to a consistent scale before training.

The target is the actual score from a future CogniSync quiz attempt. The prediction must not use features that were only available after that attempt.

### Candidate features

**Prior performance**
- Previous score for the same topic.
- Mean and median previous topic scores.
- Recent score trend.
- Score variability.
- Number of prior attempts.
- Time since last attempt.
- Prior performance in related topics, if reliable topic mapping exists.

**Quiz and content**
- Topic identifier.
- Subject identifier.
- Quiz difficulty.
- Number of questions.
- Question type distribution, if relevant.
- Source material/document identifier.
- Quiz attempt number.

**Study behaviour**
- Confirmed study duration before the quiz.
- Number of relevant study sessions.
- Time since most recent study session.
- Study timing (time of day/day of week).
- In-app engagement indicators, with idle time excluded.

**Sleep and activity, if consented and available**
- Recent sleep duration.
- Sleep timing/regularity features.
- Recent steps/activity duration.
- Activity intensity or active minutes, if available.
- Missingness and data freshness indicators.

**Academic context**
- Daily workload score.
- Class hours and class count.
- Upcoming exam count and proximity.
- Upcoming deadline count and urgency.
- Academic event load.

**Commute context, if opted in and available**
- Recent commute duration.
- Actual-versus-expected commute deviation.
- Whether a commute occurred near the candidate study window.

Features must be computed as-of the prediction timestamp. Missing values must remain missing or be imputed using a documented training-only procedure; missing data must not be treated as zero.

### Model comparison

The core experiment is:

- Previous-scores-only baseline.
- Previous-scores plus quiz/topic features.
- Context-aware model with study, sleep/activity, academic workload and commute features.

The project must report whether context features improve performance beyond the score-history baseline. Feature importance alone does not establish causation.

## 6.9 Delayed retention prediction

### Purpose

Estimate how well a student retains material after a defined interval following learning.

### Target

A delayed quiz score for the same topic, collected after a recorded interval from the relevant study/learning episode.

The delayed quiz must be distinct from the immediate quiz used to measure initial performance. Where feasible, use a different but comparable set of questions to reduce simple answer memorisation.

### Required records

- Student and topic identifiers.
- Original study-session identifiers.
- Initial quiz attempt and score, if one exists.
- Timestamp of learning/study episode.
- Delayed quiz timestamp.
- Delay interval.
- Delayed quiz score.
- Quiz difficulty and question metadata.
- Context features available before the delayed quiz.
- Whether the delayed attempt was completed within the intended window.

### Design requirements

- Define and document one or more delayed assessment intervals during the pilot.
- Do not label an immediate quiz score as retention.
- Do not infer retention from CGPA or a single final grade.
- Record missed delayed quizzes separately; do not silently treat missing attempts as zero.
- Evaluate delayed-retention prediction as a separate task from next-quiz prediction.

## 6.10 Fatigue/readiness context
The system will include a separate, non-clinical fatigue-estimation research model based on public wearable datasets. It must not diagnose fatigue or infer a medical condition.

### Initial implementation and model intent
The initial model-development work will use the public datasets in Section 8.2. The Zenodo Wearable Data and Self-Reported Fatigue Scores dataset is the primary supervised-training candidate because it pairs wearable-derived observations with self-reported fatigue information. The model must predict the fatigue label as defined by that dataset, retaining its original scale and meaning.

MMASH and PAAWS are supplementary resources for sleep/activity feature exploration, pipeline checks or external robustness analysis only where their released schemas support the intended work. Do not assume they contain a compatible fatigue ground-truth label. They must not be treated as supervised fatigue training data unless inspection confirms a suitable label and compatible timing.

Candidate algorithms are Ridge Regression for a verified continuous target, and Random Forest / XGBoost regression or classification variants according to the verified target type. Compare them with a simple target-appropriate baseline. Select using participant-level held-out evaluation, not random row splitting.

### Inputs and safeguards
Use only available, documented sleep, activity and, where justified, heart-rate features observed before the fatigue report. Do not infer fatigue labels from sensor features. Do not assume that more steps or more exercise always means more fatigue. Exclude stress and mood variables, labels and proxies completely.

If required records are missing, show insufficient data rather than a fabricated estimate. Label any public-dataset-derived output experimental until it has been validated on a consented university-student pilot with comparable inputs and fatigue labels. Show data coverage and uncertainty, provide an opt-out, and do not describe the output as clinical or diagnostic.

The fatigue model is separate from next-quiz and delayed-retention prediction. Public wearable datasets do not provide CogniSync quiz-score or retention targets. The academic prediction models remain trained on CogniSync quiz outcomes and may use authorised sleep/activity features as predictors only after adequate CogniSync outcome data exists.

## 6.11 Study-time recommendation engine

### Purpose

Rank candidate study windows for a student based on availability, predicted effectiveness and academic priorities.

### Inputs

- Confirmed weekly timetable.
- Confirmed academic calendar and deadlines.
- Commute windows and expected travel time, where available.
- Candidate study duration.
- Student's historical study patterns.
- Current context and data freshness.
- Predicted next-quiz / retention effectiveness for candidate windows.
- Academic workload features.
- Student constraints and preferences.

### Processing

1. Generate candidate windows over the selected planning horizon.
2. Remove periods occupied by classes, confirmed academic events, known commute and blocked personal time.
3. Check whether the candidate duration fits.
4. Construct candidate feature rows using information available at that candidate time.
5. Score candidates with the validated prediction model when sufficient data exists.
6. Rank remaining candidates using predicted score/effectiveness and transparent academic-priority rules.
7. Show reasons, data limitations and alternatives.

### Requirements

- **FR-REC-01:** Recommend only time windows that are free according to confirmed schedule data.
- **FR-REC-02:** Show the date, start time, duration and relevant subject/topic.
- **FR-REC-03:** Account for classes, exams, deadlines and known commute.
- **FR-REC-04:** Rank candidate windows using predicted effectiveness when model support exists.
- **FR-REC-05:** Use a transparent fallback when model confidence or student history is insufficient.
- **FR-REC-06:** Explain the main reasons for a recommendation.
- **FR-REC-07:** Allow the student to compare alternative candidate windows.
- **FR-REC-08:** Support what-if comparison while clearly stating that it is a model-based estimate, not a causal guarantee.
- **FR-REC-09:** Do not recommend a time that overlaps a confirmed event.
- **FR-REC-10:** Recalculate recommendations when new calendar, health, commute or quiz data arrives.

The recommendation engine is initially a scheduling and ranking algorithm, not a separately trained ML model.

## 6.12 Dashboard and history

The dashboard should present:

- Current next-quiz prediction, where enough data exists.
- Delayed-retention prediction, where enough data exists.
- Prediction interval/uncertainty and data coverage.
- Upcoming recommended study windows.
- Today's and upcoming academic workload.
- Confirmed classes, exams and deadlines.
- Recent confirmed study sessions.
- Quiz history and topic-level score trends.
- Sleep/activity connection state and last sync, if connected.
- Commute tracking state and recent derived commute summaries, if enabled.
- Clear separation between measured, observed, confirmed, calculated and predicted values.

The dashboard must not contain stress or mood displays.

## 6.13 What-if simulator and explainability

- Allow students to compare candidate study times or durations.
- Recompute features for each scenario without changing historical records.
- Explain the strongest model input categories where the model supports such explanation.
- Use SHAP or a compatible feature-attribution method for supported tabular models, after checking explanation validity.
- Explain that feature attribution describes model behaviour, not causal effects.
- Show uncertainty and data-quality limitations.
- Do not present feature attribution as proof that sleep, commute or workload caused a score change.

## 6.14 Textbook meaning-preservation checker

### Purpose

Check whether an AI-generated simplified explanation appears to preserve the meaning of its source textbook passage.

This is a separate AI research feature; it is not part of the numerical quiz-score prediction model.

### Inputs

- Original source passage retrieved from the student's uploaded textbook.
- Simplified explanation generated by the study assistant.
- Source page/document metadata.

### Processing

1. Split the simplified explanation into atomic factual claims.
2. Retrieve or align the most relevant source sentence(s).
3. Use a pretrained Natural Language Inference (NLI) model to classify each claim as supported, contradicted or insufficiently supported.
4. Run targeted checks for numbers, units, dates, negation, conditions, comparisons and technical terms.
5. Flag potential meaning changes and show the relevant source evidence.
6. Optionally request a corrected simplification and run the checks again.

### Model choice

Initial candidate: a pretrained DeBERTa-v3 MNLI/NLI checkpoint (for example, a suitable `deberta-v3-base` MNLI-finetuned checkpoint), subject to model-card, licence, inference-cost and compatibility review.

The team will not train an NLI foundation model from scratch. The uploaded Newsela and WikiLarge examples are simplification pairs and can support simplification experiments/evaluation, but their deletion/insertion/substitution labels are not equivalent to supported/contradicted/insufficiently-supported factual labels.

A separate human-labelled evaluation set is required to assess the checker. It should include:
- Supported claims.
- Contradicted claims.
- Insufficiently supported claims.
- Number/unit changes.
- Negation changes.
- Condition/exception changes.
- Technical-term changes.

### Requirements

- **FR-MEAN-01:** Compare a simplified claim against the actual source passage.
- **FR-MEAN-02:** Return supported, contradicted or insufficiently-supported classifications.
- **FR-MEAN-03:** Show source evidence and reason for each flag.
- **FR-MEAN-04:** Check numbers, units, dates, negation, conditions and technical terms.
- **FR-MEAN-05:** Mark output as advisory; do not claim perfect factual verification.
- **FR-MEAN-06:** Preserve source document/page references.
- **FR-MEAN-07:** Evaluate precision, recall, F1 and false-alarm rate on a human-labelled set.
- **FR-MEAN-08:** Keep meaning-checker evaluation separate from score-prediction evaluation.

---

# 7. Student journeys

## 7.1 Onboarding

1. Student creates an account.
2. Student enters basic academic profile and timezone.
3. Student may upload a weekly timetable.
4. Student may upload an academic calendar.
5. CogniSync extracts events and asks the student to review them.
6. Student may connect Google Health with explicit consent.
7. Student may optionally configure Android commute tracking.
8. Student can begin using PDFs, summaries and quizzes without completing optional integrations.

## 7.2 Study and quiz journey

1. Student uploads a textbook or course PDF.
2. CogniSync extracts and indexes the content.
3. Student selects a subject/topic.
4. CogniSync generates a grounded summary.
5. Student studies within CogniSync.
6. CogniSync observes relevant in-app events and derives a candidate study session.
7. Student confirms/corrects the session and topic.
8. Student takes a generated quiz.
9. CogniSync stores the actual score and links it to the relevant study context.
10. CogniSync updates the next-score prediction history.
11. CogniSync schedules or offers a delayed quiz to measure retention.

## 7.3 Recommendation journey

1. CogniSync reads confirmed classes and academic events.
2. The workload engine calculates daily and future workload features.
3. Commute periods are included if commute tracking is enabled.
4. CogniSync identifies candidate free windows.
5. The model scores candidate windows when enough data exists.
6. The recommendation engine ranks and explains the windows.
7. The student accepts, dismisses or modifies a suggestion.

## 7.4 Meaning-checker journey

1. Student requests a simplified explanation.
2. CogniSync retrieves the original textbook passage.
3. The language model generates a simplified explanation.
4. The checker splits it into claims and compares them with the source.
5. CogniSync displays flags and supporting source evidence.
6. Student can inspect the original passage and request a revision.

---

# 8. Data strategy and dataset specification

## 8.1 Data principles

- Collect only data needed for defined product functions.
- Keep source, timestamp, consent state and confidence/provenance.
- Separate measured, observed, student-confirmed, calculated and predicted values.
- Do not use missing data as zero.
- Prevent target leakage and post-outcome feature contamination.
- Keep student-level records isolated in evaluation where required.
- Respect dataset licences and API terms.
- Do not combine datasets merely because they share a column name.
- Do not treat GPA, final result, immediate quiz score and delayed retention as interchangeable targets.

## 8.2 Selected datasets

The project will use the following dataset resources for the purposes stated: OULAD for the academic benchmark; Zenodo as the primary public supervised fatigue-label candidate; MMASH and PAAWS as supplementary health-data research resources subject to label/schema verification; and Newsela/WikiLarge for meaning-preservation support.

### Dataset A — OULAD (Open University Learning Analytics Dataset)

**Project role:** Offline benchmark for next-assessment score prediction.

Uploaded files:
- `assessments.csv`
- `courses.csv`
- `studentAssessment.csv`
- `studentInfo.csv`
- `studentRegistration.csv`
- `vle.csv`
- `OULAD.names`

Relevant fields include:
- Assessment identifiers, type, date and weight.
- Student assessment submission dates and scores.
- Course/module and presentation identifiers.
- Student course participation and final-result metadata.
- Registration and withdrawal dates.
- VLE resource metadata.

The uploaded `studentAssessment.csv` contains repeated student-assessment score records. This supports constructing chronological assessment histories and predicting a later assessment score from earlier information.

The uploaded `vle.csv` is resource metadata. The separate student-level VLE interaction log is not part of the uploaded file set; therefore individual VLE engagement features must not be assumed available from the current upload.

#### OULAD use restrictions and methodology

- Use OULAD to build an offline benchmark experiment.
- Construct one prediction example per eligible student/course assessment where prior history exists.
- Sort assessments by actual assessment date and use only information available before the target assessment.
- Exclude target assessment score and all later assessment information from the feature row.
- Consider assessment type, assessment weight, days to assessment and course context where valid.
- Use previous score, historical mean, score trend, score variance and attempt count as candidate features.
- Handle missing scores, banked assessments, withdrawals and course/presentation boundaries explicitly.
- Do not treat final-result categories or aggregate outcomes as repeated quiz targets.
- Do not assume OULAD's assessments are identical to CogniSync quizzes.
- Do not automatically deploy the OULAD-trained model on CogniSync users.
- Report the domain mismatch and benchmark limitations.

### Dataset B — Public wearable and fatigue-related datasets

**Project role:** Research training and evaluation resources for the separate, non-clinical fatigue-estimation component. These datasets are not academic-performance datasets and must not be used to train next-quiz or delayed-retention targets.

#### B1 — Zenodo: Wearable Data and Self-Reported Fatigue Scores
Reference: https://zenodo.org/records/8018238

**Intended role:** Primary candidate for supervised fatigue-estimation training because it includes wearable-derived sleep/activity/physiological measurements paired with self-reported fatigue information.

Potential inputs, subject to the released schema:
- Sleep-related measurements.
- Physical activity / Fitbit-derived measures.
- Heart-rate measurements where available.

Potential target:
- The dataset's own self-reported fatigue score or category, using its original definition and scale.

Before training, inspect the files and documentation to establish the exact fatigue instrument, score range, observation cadence, participant coverage, missingness and valid pairing between sensor windows and fatigue reports. Align predictor windows strictly before the corresponding fatigue report to avoid temporal leakage. Do not reinterpret the label as a clinical diagnosis.

#### B2 — MMASH (Multilevel Monitoring of Activity and Sleep in Healthy people)
Reference: https://physionet.org/content/mmash/1.0.0/

**Intended role:** Supplementary sleep/activity feature exploration and external robustness analysis. It contains wearable/sensor and sleep-related measurements from a small cohort; it is not assumed to provide a directly compatible fatigue target.

Use only variables and labels confirmed in its documentation. Do not use stress-related fields or derive stress labels. Do not treat MMASH as supervised fatigue training data unless inspection confirms a suitable fatigue ground-truth label with compatible timing and semantics. Its small cohort limits generalisation claims.

#### B3 — PAAWS Study Dataset
Reference: https://www.paawsstudy.org/data.html

**Intended role:** Supplementary sleep/activity and wearable-data validation, subject to the actual released files, annotations, access conditions and licence.

Use only data elements explicitly present in the accessible release. Do not assume activity annotations or sleep recordings are fatigue labels. It may support feature-pipeline checks or external evaluation of relevant sensor-derived features, but it is not a supervised fatigue dataset unless a compatible fatigue target is verified.

#### Cross-dataset rules
- Verify current availability, access requirements, data dictionaries, consent terms and licences before download or use.
- Record dataset version, source URL, access date, participant population, device/sensor type, sampling frequency and label definition.
- Do not merge datasets unless participant identity, units, time windows, feature definitions and target semantics are demonstrably compatible.
- Keep participant-level records grouped in train/validation/test splits to prevent participant leakage.
- Report cohort size and population limitations; do not assume these cohorts represent university students.
- Exclude stress and mood variables, labels and proxies at ingestion.
- Do not infer missing fatigue labels from sleep duration, activity, heart rate or other sensor values.
- These datasets support fatigue-estimation research only. They do not remove the need for a consented university-student validation dataset before student-facing use.

### Dataset C — Newsela and WikiLarge simplification examples

Uploaded files:
- `newsela_deletion.json`
- `newsela_insertion.json`
- `newsela_substitution.json`
- `wikilarge_deletion.json`
- `wikilarge_insertion.json`
- `wikilarge_substitution.json`

**Project role:** Supporting material for text simplification experiments and evaluation of the meaning-preservation feature.

These files contain complex/simplified text pairs and edit-operation metadata. They are not student performance datasets and must not be used for quiz-score or retention prediction.

Their edit-operation labels do not by themselves provide the full factual-entailment labels required by the meaning checker. A human-labelled claim-level evaluation set is still required.

Before use, verify dataset provenance, licence, permitted use, schema consistency and any redistribution restrictions. Do not redistribute raw dataset contents unless permitted.

## 8.3 Datasets explicitly not selected

### Student Lifestyle Dataset

The uploaded `student_lifestyle_dataset.csv` includes lifestyle-related fields and a broad academic outcome such as GPA. It is not selected as the primary score-prediction dataset because it does not provide repeated topic-level quiz attempts linked to study sessions and timestamps. Its stress-related field is excluded and must not enter CogniSync.

It may be used for exploratory analysis only if separately approved, properly licensed and useful to a clearly defined question. It is not required for the v1.2 training plan.

### SciQ-style Parquet dataset

The uploaded train/validation/test Parquet files contain multiple-choice science questions, distractors, answers and supporting passages. The team has decided not to use this dataset. It is excluded from the project data plan and model training.

## 8.4 CogniSync-collected dataset — essential future dataset

OULAD cannot supply the specific link between CogniSync users' sleep/activity, commute, academic workload, study sessions and CogniSync quiz outcomes. CogniSync must therefore collect its own consented dataset.

### Core entities

- Student.
- Subject and topic.
- Uploaded document and source passage.
- Study event.
- Candidate study session.
- Student-confirmed study session.
- Quiz and quiz question.
- Quiz attempt.
- Delayed quiz attempt.
- Health observation.
- Academic timetable event.
- Academic calendar event.
- Workload feature snapshot.
- Commute event.
- Prediction record.
- Recommendation record.
- Consent and integration state.

### Minimum quiz-attempt record

- Student pseudonymous ID.
- Subject/topic ID.
- Quiz ID and attempt ID.
- Quiz timestamp.
- Actual score and maximum score.
- Normalised score.
- Question count and question-level outcomes.
- Difficulty metadata.
- Source document/topic reference.
- Relevant prior study-session IDs, where available.
- Prediction generated before the attempt, if one exists.
- Model version and feature snapshot used for that prediction.

### Minimum study-session record

- Student pseudonymous ID.
- Start/end timestamps.
- Estimated active duration.
- Confirmation status.
- Student-corrected duration, if any.
- Subject/topic.
- Observed event references.
- Sessionisation method/version.
- Data confidence.

### Minimum context snapshot

For each prediction or quiz attempt, preserve the feature values and their timestamps as they were known at prediction time:
- Prior score history.
- Study history.
- Sleep/activity features where authorised and available.
- Academic workload features.
- Commute features where opted in and available.
- Missingness and data freshness.
- Feature-generation version.

### Delayed retention record

- Original learning/study episode.
- Topic.
- Delay interval.
- Delayed quiz timestamp.
- Delayed quiz score.
- Question/quiz form metadata.
- Whether the intended delay window was met.

## 8.5 Data availability and cold-start policy

At launch, CogniSync will not have enough user-collected records to train a reliable context-aware model.

Therefore:
- OULAD supplies an offline benchmark only.
- A score-history baseline may be used when the student has sufficient previous CogniSync quiz attempts.
- For a new student or topic with no history, show an insufficient-history state or a clearly labelled coarse fallback rather than a falsely precise personalised prediction.
- Do not claim that an OULAD model is calibrated for CogniSync quiz outcomes.
- Accumulate consented CogniSync data before training and validating the context-aware model.
- Delay personal model refitting until a configurable minimum quantity and quality of individual records is reached.

---

# 9. Model strategy — exact models and training plan

## 9.1 Model inventory

The planned models and algorithms are:

| ID | Component | Exact initial model/algorithm | Training status |
|---|---|---|---|
| M1 | OULAD benchmark | Historical mean predictor | Baseline calculation |
| M2 | OULAD benchmark | Last-score predictor | Baseline calculation |
| M3 | OULAD benchmark | Ridge Regression | Train on OULAD chronological examples |
| M4 | OULAD benchmark | Random Forest Regressor | Train on OULAD chronological examples |
| M5 | OULAD benchmark | XGBoost Regressor | Train if dependency, sample size and validation support it |
| M6 | CogniSync next-quiz score | Ridge Regression | Train on CogniSync-collected quiz/context records when sufficient data exists |
| M7 | CogniSync next-quiz score | Random Forest Regressor | Train and compare on CogniSync-collected records |
| M8 | CogniSync next-quiz score | XGBoost Regressor | Train and compare on CogniSync-collected records |
| M9 | Delayed retention | Ridge Regression | Train on CogniSync delayed-quiz records |
| M10 | Delayed retention | Random Forest Regressor | Train and compare on CogniSync delayed-quiz records |
| M11 | Delayed retention | XGBoost Regressor | Train and compare on CogniSync delayed-quiz records |
| M12 | Personalisation | Per-student bias/residual correction | Update from each student's prediction errors |
| M13 | Textbook meaning checker | Pretrained DeBERTa-v3 MNLI/NLI candidate | Use pretrained checkpoint; evaluate, do not train from scratch |
| M14 | Academic workload | Transparent weighted/rule-based scoring | No ML training |
| M15 | Commute context | Google Maps expected duration + Android detected duration comparison | No ML training initially |
| M16 | Study-window recommendations | Availability filtering + model-based candidate ranking | No separate ML training initially |
| M17 | Fatigue estimate | Ridge Regression (continuous target); Random Forest and XGBoost (regression/classification according to verified label) | Train/evaluate primarily on Zenodo wearable + self-reported fatigue data; use MMASH/PAAWS only for supported supplementary analyses |
| M18 | Readiness context | Experimental fatigue estimate with data-coverage/uncertainty display | No separate readiness model |

These are candidate model families, not a promise that every algorithm will be deployed. Model selection is based on held-out evaluation. A simpler model must be preferred if it performs similarly and is easier to interpret, maintain and validate.

## 9.2 OULAD benchmark models

### Baselines

1. **Historical mean:** Predict the mean of the student's previous eligible assessment scores.
2. **Last score:** Predict the student's most recent eligible assessment score.

### Trainable candidates

3. **Ridge Regression:** Regularised linear regression baseline.
4. **Random Forest Regressor:** Non-linear tree ensemble.
5. **XGBoost Regressor:** Gradient-boosted tree model, if the development environment and validation results justify it.

### OULAD feature examples

- Previous score.
- Mean/median of previous scores.
- Recent score trend.
- Score standard deviation.
- Number of previous assessments.
- Time since previous assessment.
- Assessment type.
- Assessment weight.
- Days to target assessment.
- Course/module and presentation context, encoded without leakage.
- Registration/withdrawal information only where known before the target assessment and appropriate to the task.

### Evaluation

- Use chronological assessment ordering.
- Ensure target and future assessments do not enter the feature set.
- Use student-level and/or course-presentation-aware holdouts as appropriate.
- Report MAE and RMSE; report R² only where meaningful.
- Compare every trained model with historical-mean and last-score baselines.
- Record split strategy, random seeds, preprocessing and model versions.
- Do not use random row splits that allow later records from the same learning trajectory to leak into earlier predictions.

The OULAD model is a research benchmark. It is not automatically a production CogniSync model.

## 9.3 CogniSync next-quiz score model

### Target

Actual next CogniSync quiz score, on a normalised 0–100 scale.

### Candidate model families

- Ridge Regression.
- Random Forest Regressor.
- XGBoost Regressor.

### Baselines

- Last score for the same topic.
- Mean of previous scores for the same topic.
- Overall student quiz mean, only when topic history is unavailable and the fallback is clearly labelled.

### Required comparison

- **Score-only model:** previous scores and quiz/topic history.
- **Context-aware model:** score-only features plus study, sleep/activity, academic workload and commute features where available.
- **Ablation experiments:** add/remove feature groups to measure their incremental predictive value.

The project must report whether the context-aware model improves prediction over the score-only model. A feature group that does not improve held-out performance should not be retained merely because it sounds useful.

## 9.4 Delayed retention model

### Target

Actual delayed quiz score for the same topic after a recorded interval.

### Candidate model families

- Ridge Regression.
- Random Forest Regressor.
- XGBoost Regressor.

### Baselines

- Most recent immediate score for that topic.
- Mean of previous delayed scores for that topic, when available.
- A simple decay/retention baseline may be tested only if its assumptions and parameters are documented.

The delayed retention model is separate from next-quiz prediction because the target and timing are different. It must be trained only after enough delayed outcomes have been collected.

## 9.5 Personalisation and calibration

Personalisation should be gradual.

Initial approach:
- Start with a shared CogniSync model once sufficient pooled CogniSync training data exists.
- For students with limited history, use the shared model with an explicit uncertainty/data-coverage warning.
- Track each prediction and its eventual actual score.
- Calculate residual error: `predicted_score - actual_score`.
- Apply a simple per-student bias correction (for example, a running or exponentially weighted mean residual) when enough outcomes exist.
- Validate calibration on later chronological records.

Only consider a separately refitted per-student Ridge model or another regularised personal model when the individual student has enough varied, high-quality records. Do not train complex individual models on a handful of quiz attempts.

Global training, personal adaptation and residual calibration must be versioned and evaluated separately.

## 9.6 Fatigue-estimation model

### Objective and target
Estimate a non-clinical fatigue score/category from recent wearable-derived sleep and activity observations. The target is the fatigue label actually recorded in the Zenodo dataset; preserve its original scale and semantics. Do not invent a new label or convert it into a medical diagnosis.

### Training data
- **Primary supervised candidate:** Zenodo Wearable Data and Self-Reported Fatigue Scores (Section 8.2, Dataset B1).
- **Supplementary resources:** MMASH and PAAWS (Sections 8.2, B2-B3), only for feature exploration, pipeline checks or external robustness analyses supported by their actual released schema. They are not assumed to have compatible fatigue labels.
- OULAD, Newsela/WikiLarge and the excluded Student Lifestyle/SciQ resources are not fatigue-target training sources.

### Candidate algorithms
- Ridge Regression if the verified fatigue target is continuous.
- Random Forest Regressor / Classifier according to target type.
- XGBoost Regressor / Classifier according to target type, if sample size and validation justify it.
- A simple mean/majority or last-observation baseline appropriate to the target.

### Candidate input features
Use only fields confirmed in the dataset and available before the fatigue report: sleep duration/timing, sleep regularity or stages if available, activity duration/steps/intensity if available, heart-rate summaries if available and justified, and data-coverage/freshness indicators. Exclude stress and mood fields, labels and proxies. Do not treat greater activity as automatically implying greater fatigue. Do not infer fatigue labels from predictor features.

### Training and evaluation protocol
1. Inspect dataset documentation and files; establish label definition, units, timing, participant count and data quality.
2. Align sensor windows to fatigue-report timestamps, using only pre-report observations.
3. Split by participant, not randomly by row. Where feasible, retain a held-out participant test set.
4. Fit preprocessing only on training folds; handle missingness explicitly.
5. Compare candidate models with the appropriate baseline.
6. Report MAE/RMSE for continuous targets, or macro-F1/precision/recall and class balance for categorical targets. Include calibration/uncertainty checks where appropriate.
7. Perform sleep-only, activity-only and combined-feature ablations where supported.
8. Document dataset shift, sensor/device differences and population limitations.

### Deployment gate
A model trained on public datasets is an experimental research model, not automatically suitable for university students. Before enabling a student-facing fatigue estimate, collect a consented university-student pilot with comparable sensor inputs and a compatible fatigue label, then evaluate generalisation and calibration on held-out students. Until this gate is met, keep the feature disabled or clearly marked experimental, show uncertainty and data coverage, and provide an opt-out.

### Separation from academic prediction
This model predicts only its defined fatigue target. It does not predict quiz scores or retention. CogniSync's next-quiz and delayed-retention models remain trained on CogniSync quiz outcomes; authorised health features may be included as predictors only after adequate CogniSync data has been collected and evaluated.

## 9.7 Academic workload engine is not a trained model

The workload score is calculated from confirmed timetable/calendar data using transparent configurable rules. The score and its component features are passed into the context-aware prediction model.

No separate ML training dataset is required for:
- Class hours.
- Exam proximity.
- Number of upcoming exams.
- Deadline proximity.
- Number of upcoming deadlines.
- Confirmed academic event density.

Student feedback can be used to evaluate and calibrate the workload score, but it is not a substitute for score-prediction labels.

## 9.8 Commute engine is not a trained model

The initial commute component compares:
- Actual detected trip duration.
- Google Maps expected route duration for the relevant route/departure context.

Derived commute features may be passed into the score-prediction model when available. No custom Google Maps/traffic model is required.

## 9.9 Textbook meaning checker is not trained from scratch

Use a suitable pretrained NLI checkpoint, initially a DeBERTa-v3 MNLI/NLI candidate, after verifying its licence, model card and inference requirements.

Newsela/WikiLarge examples support simplification experiments but do not provide the full claim-level entailment labels. Create a human-labelled CogniSync evaluation set.

Fine-tuning the NLI model is not part of the initial commitment. It may be considered only if the team later collects a sufficiently large, high-quality labelled dataset and demonstrates a need.

## 9.10 Model governance

For every model version, store:
- Model name/type and version.
- Training dataset version.
- Feature schema/version.
- Training timestamp.
- Data split methodology.
- Evaluation metrics.
- Hyperparameters.
- Random seed.
- Known limitations.
- Deployment status.
- Calibration status.

Predictions must store model version and a feature snapshot sufficient to reproduce the prediction where privacy and storage policy permit.

---

# 10. High-level technical architecture

## 10.1 Main components

1. **Web frontend**
   - Authentication.
   - Dashboard.
   - Study workspace.
   - Quiz interface.
   - Timetable/calendar review.
   - Recommendation and history views.
   - Consent and integration settings.

2. **Backend API**
   - Authentication and user management.
   - Study documents and quiz services.
   - Session/event ingestion.
   - Health OAuth and sync service.
   - Academic calendar/timetable service.
   - Workload feature service.
   - Commute event service.
   - Prediction and recommendation APIs.
   - Meaning-checker service.

3. **Android companion**
   - Home/college geofence registration.
   - Background transition handling.
   - Minimal commute event capture.
   - Permission and tracking controls.
   - Secure backend communication.

4. **Data layer**
   - Relational database for users, schedules, events, sessions, quizzes, predictions and consent state.
   - Object storage for uploaded documents.
   - Vector store for retrieved document chunks.
   - Model/artifact storage for trained model versions.

5. **ML and AI layer**
   - Tabular model training/evaluation pipeline.
   - Prediction service.
   - Personalisation/calibration service.
   - RAG summarisation and quiz generation.
   - Pretrained NLI meaning checker.

## 10.2 Suggested technology direction

The final stack may be confirmed during technical design. A reasonable starting point is:

- Backend: Python with Flask or FastAPI.
- Frontend: modern web frontend; retain a clear API boundary.
- Database: PostgreSQL or another relational database.
- Document extraction: PyMuPDF plus OCR fallback.
- Embeddings/vector retrieval: selected embedding model and ChromaDB or equivalent.
- Tabular ML: scikit-learn, with XGBoost if selected.
- Explainability: SHAP for compatible tabular models.
- Android companion: Kotlin/native Android or a suitable Android implementation.
- Routing: Google Maps Routes API.
- Health: Google Health API via server-side OAuth.
- NLI: pretrained DeBERTa-v3 MNLI/NLI candidate.

These are proposed implementation choices, not all mandatory vendor decisions.

## 10.3 Data flow

1. Student supplies schedules and study PDFs.
2. Schedule ingestion creates draft events for student confirmation.
3. Workload engine derives day/week features from confirmed events.
4. Optional health sync imports consented sleep/activity observations.
5. Optional Android commute component creates derived trip records.
6. Study workspace observes in-app events and creates candidate sessions.
7. Student confirms/corrects sessions.
8. Quiz service generates quizzes and records actual attempts.
9. Feature pipeline builds a point-in-time feature snapshot.
10. Prediction service generates next-quiz or delayed-retention predictions.
11. Recommendation engine filters available time and ranks candidate windows.
12. Actual outcomes are compared with predictions for evaluation and calibration.

---

# 11. Privacy, consent and security

## 11.1 Data minimisation

- Collect only the data needed for defined features.
- Do not collect stress or mood.
- Do not collect continuous raw GPS routes.
- Do not collect health data unless the student explicitly connects and grants consent.
- Do not require health or commute integration.
- Keep source provenance and purpose for imported data.

## 11.2 Consent and control

- Explain each health data category before requesting access.
- Explain Android location/geofence use before permission prompts.
- Keep commute tracking off by default.
- Allow pausing, disconnecting and deleting integration-derived records.
- Handle OAuth revocation and token expiry.
- Allow students to review/correct extracted academic events and candidate study sessions.

## 11.3 Security

- Encrypt data in transit and at rest.
- Keep API secrets and OAuth tokens server-side.
- Apply least-privilege access controls.
- Use pseudonymous student IDs in ML datasets.
- Separate development/test data from production personal data.
- Restrict access to uploaded documents and health/commute records.
- Log sensitive administrative access.
- Establish backup, retention and deletion procedures.

## 11.4 External AI services

- Do not send unnecessary personal or health data to LLM providers.
- Retrieve only relevant textbook passages for summarisation and quiz generation.
- Review provider retention and data-use terms.
- Avoid including personally identifiable student information in prompts.
- Keep the meaning checker anchored to the source passage.

## 11.5 Research and dataset governance

- Verify OULAD and Newsela/WikiLarge terms and licences before use.
- Follow dataset attribution requirements.
- Do not redistribute source datasets unless their licences permit it.
- Obtain appropriate consent and institutional approval for collecting student pilot data.
- Report cohort limitations and avoid overstating generalisability.

---

# 12. Non-functional requirements

## 12.1 Reliability

- API failures must not corrupt student records.
- Sync operations must be retryable and idempotent where possible.
- Duplicate health and commute events must be detected.
- Missing integrations must not break the core application.

## 12.2 Performance

- Dashboard and history queries should be paginated where needed.
- Model inference should be responsive for interactive use.
- Long-running PDF ingestion and model training should run asynchronously.
- Model training must not block normal study/quiz usage.

## 12.3 Explainability

- Display model uncertainty and data availability.
- Distinguish prediction from measured score.
- Explain workload score contributors.
- Explain recommendation constraints and ranking factors.
- Do not present correlations as causal effects.

## 12.4 Accessibility and usability

- Clear language for students.
- Responsive web interface.
- Review/correction flows for extracted events.
- Optional integrations must be easy to skip.
- No excessive prompts after every study event.

## 12.5 Maintainability

- Separate ingestion, feature engineering, model training, inference and recommendation modules.
- Version feature schemas and model artifacts.
- Keep reproducible training scripts and evaluation reports.
- Add automated tests for point-in-time feature generation and leakage prevention.

---

# 13. Evaluation plan

## 13.1 OULAD benchmark evaluation

Compare:
- Historical mean.
- Last score.
- Ridge Regression.
- Random Forest Regressor.
- XGBoost Regressor, if used.

Metrics:
- Mean Absolute Error (MAE).
- Root Mean Squared Error (RMSE).
- R² where meaningful.
- Error distribution by assessment type and course/presentation where sample size supports it.

Use chronological and student-aware evaluation. Report data filtering and exclusions.

## 13.2 CogniSync next-quiz prediction

Compare:
1. Last-score baseline.
2. Topic mean baseline.
3. Previous-scores-only Ridge/Random Forest/XGBoost.
4. Context-aware models with study and lifestyle/context features.

Report:
- MAE.
- RMSE.
- R² where meaningful.
- Prediction interval coverage where supported.
- Mean signed error / bias.
- Results by amount of student history.
- Results by topic/subject where sample size supports it.
- Feature-group ablations.

Use chronological evaluation and student-level holdouts where appropriate. Do not let attempts from the future appear in the features for an earlier attempt.

## 13.3 Delayed retention evaluation

- Evaluate delayed score as a separate target.
- Compare against immediate score and simple historical baselines.
- Report MAE/RMSE and calibration where supported.
- Report delay interval and completion/missingness.
- Avoid treating non-completion as a zero score.

## 13.4 Personalisation and calibration

Compare:
- Shared/global model only.
- Shared model plus per-student bias correction.
- Shared model plus personal refitting, if sufficient records exist.

Evaluate chronological MAE, RMSE and mean signed error. Report performance by amount of individual data.

## 13.5 Workload engine evaluation

- Compare calculated events with student-confirmed timetable/calendar records.
- Evaluate event extraction accuracy separately from workload calculation.
- Ask students to rate whether workload bands reflect their perceived scheduled workload, as optional research feedback.
- Evaluate whether workload features improve held-out score prediction; do not assume that they will.

## 13.6 Commute evaluation

- Compare detected trips against student-confirmed trips.
- Evaluate missed trips, false detections and duration error.
- Compare actual detected duration with the corresponding Maps estimate.
- Do not infer commute effects on performance without an appropriately controlled analysis.

## 13.7 Meaning-preservation checker evaluation

Use a human-labelled claim-level dataset. Report:
- Precision.
- Recall.
- F1.
- Confusion matrix.
- False-alarm rate.
- Results for numbers, units, negation, conditions and technical terms.

Compare the NLI model with targeted checks and combined approaches. Treat checker output as advisory.

---

# 14. Acceptance criteria

The release is not complete unless the relevant criteria below are met.

## 14.1 Core platform

- Students can register and securely access their account.
- Core features work without wearable or commute integration.
- Student records are correctly isolated.

## 14.2 Data and model

- OULAD benchmark pipeline is reproducible.
- No target leakage is detected in feature-generation tests.
- Baseline and candidate model metrics are reported.
- CogniSync quiz attempts are stored with topic, score and timestamp.
- Delayed quiz attempts are distinguishable from immediate attempts.
- Predictions store model version and point-in-time feature snapshot.
- Missing values are not silently interpreted as zero.
- Insufficient-history predictions are clearly labelled.

## 14.3 Academic workload

- Confirmed timetable and calendar events generate daily and rolling workload features.
- Exam proximity and deadline urgency are calculated.
- Overlapping events are not double-counted.
- Student corrections trigger recalculation.
- Workload contributors are visible.

## 14.4 Health integration

- OAuth consent is explicit.
- Tokens remain server-side.
- Sync state and last successful sync are visible.
- Disconnect/revocation is handled.
- Missing data does not break recommendations.

## 14.5 Commute

- Android tracking is opt-in.
- Home/college geofences can be configured.
- Student can pause, correct and delete commute records.
- Only derived commute data is retained; no continuous route history is stored.
- Maps usage has quota/billing controls.

## 14.6 Study tools

- PDFs can be uploaded, indexed and deleted.
- Summaries include source references where available.
- Quizzes are grounded in uploaded materials.
- Attempts and actual scores are stored.
- Study-session capture distinguishes observed events from confirmed sessions.

## 14.7 Meaning checker

- Simplified claims are compared against source passages.
- Flags include evidence and reason.
- Human-labelled evaluation is performed.
- The interface does not claim perfect verification.

---

# 15. Delivery roadmap

## Phase 0 — Technical feasibility and data audit

- Validate OULAD schemas, licences and preprocessing.
- Build OULAD chronological benchmark dataset.
- Train baseline and candidate benchmark models.
- Verify Google Health API access, scopes, source compatibility and OAuth constraints.
- Verify Maps Routes API implementation and usage limits.
- Prototype Android geofence reliability.
- Test NLI checkpoint licence, model card and inference requirements.
- Define consent and pilot-data collection protocol.

**Exit criteria:** Feasibility findings, dataset audit, baseline benchmark report and architecture decisions documented.

## Phase 1 — Core platform and study tools

- Authentication/profile.
- PDF upload and ingestion.
- RAG-based summarisation.
- Grounded quiz generation.
- Quiz attempt storage.
- In-app event tracking and session confirmation.
- Initial dashboard/history.

**Exit criteria:** A student can upload material, study, take quizzes and see recorded results.

## Phase 2 — Academic schedule and workload

- Timetable/calendar upload.
- Event extraction and confirmation.
- Academic workload feature engine.
- Daily and 7/14-day workload views.
- Candidate study-window generation from confirmed availability.

**Exit criteria:** Recommendations respect confirmed classes, exams and deadlines.

## Phase 3 — Score prediction and pilot data

- OULAD benchmark completion.
- CogniSync score-history baselines.
- Point-in-time feature pipeline.
- Next-quiz prediction experiments as data accumulates.
- Delayed quiz workflow.
- Prediction logging and calibration.

**Exit criteria:** Reproducible baseline and a defined plan for context-aware evaluation. Do not claim context-model readiness until enough data exists.

## Phase 4 — Health and commute context

- Google Health API integration.
- Source compatibility matrix.
- Android companion geofencing.
- Google Maps expected-duration comparison.
- Sync, consent and deletion controls.
- Feature integration into model pipeline.

**Exit criteria:** Optional integrations work reliably and do not block core functionality.

## Phase 5 — Context-aware modelling and personalisation

- Train context-aware next-quiz model on CogniSync data.
- Train delayed-retention model on delayed quiz outcomes.
- Run feature ablations.
- Add per-student residual correction.
- Consider personal refitting only with sufficient records.
- Validate uncertainty and recommendation ranking.

**Exit criteria:** Evidence-based comparison against score-only baselines.

## Phase 6 — Meaning preservation and final evaluation

- Integrate pretrained NLI checker.
- Build human-labelled evaluation set.
- Evaluate simplification and meaning preservation.
- Complete model and product evaluation.
- Document limitations and research findings.

**Exit criteria:** Meaning-checker report and final evaluation report.

---

# 16. Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Too few CogniSync quiz attempts | Context-aware model cannot be trained reliably | Start with OULAD benchmark and simple baselines; collect pilot data |
| OULAD differs from CogniSync quizzes | Benchmark does not transfer | Keep it as benchmark; do not claim direct deployment validity |
| Delayed quiz completion is low | Retention labels are sparse | Keep follow-up workflow short; report missingness; do not treat missing as zero |
| Wearable sources expose different fields | Inconsistent health coverage | Validate source compatibility; use optional features and missingness indicators |
| Google Health API access/terms change | Integration may be blocked or limited | Phase 0 proof of concept; verify scopes and current requirements |
| OAuth testing constraints | Reconnection or user-limit friction | Document testing-mode restrictions and production verification requirements |
| Android background restrictions | Commute detection may miss transitions | Prototype early; permission education; manual correction and pause controls |
| Maps API usage costs | Unexpected expense | Quotas, budget alerts, usage caps and caching where permitted |
| Academic PDFs are ambiguous | Incorrect schedule/workload | Student review and correction before use |
| Calendar workload does not reflect effort | Workload estimate is incomplete | Label scheduled workload; optional effort/backlog input |
| In-app activity overestimates study | Noisy study duration | Sessionisation, visibility signals and student confirmation |
| NLI checker false positives/negatives | Incorrect warnings or missed errors | Human-labelled evaluation; advisory output; targeted checks |
| Small pilot sample | Weak generalisation | Report uncertainty and limitations; avoid broad claims |
| Data leakage | Inflated model metrics | Point-in-time features, chronological splits and automated tests |

---

# 17. Success metrics

## Product metrics

- Percentage of students who successfully upload and confirm a timetable/calendar.
- Percentage of quiz attempts linked to a topic and relevant study context.
- Study-session confirmation/correction rate.
- Health integration sync success rate among students who opt in.
- Commute detection precision among students who opt in.
- Recommendation acceptance and dismissal rates.
- Delayed quiz completion rate.

## ML metrics

- OULAD benchmark MAE/RMSE.
- CogniSync next-quiz MAE/RMSE versus previous-score baselines.
- Context-aware improvement (or lack of improvement) over score-only model.
- Delayed-retention MAE/RMSE.
- Prediction bias and calibration.
- Performance by amount of student history.
- Meaning-checker precision, recall, F1 and false-alarm rate.

Do not set arbitrary accuracy targets before establishing a baseline and evaluating data quality. Report negative or inconclusive results.

---

# 18. Assumptions and decisions to validate

1. Google Health API is the preferred health-data route, but access, scopes, source coverage and current terms require a proof of concept.
2. The direct API route may not expose all records from every watch brand or fitness app.
3. Android companion development is required for reliable background geofence commute detection.
4. Google Maps Routes API usage and pricing must be checked before release.
5. OULAD is an offline benchmark, not the deployed CogniSync training population.
6. The exact delayed-retention interval(s) must be selected during pilot design.
7. The amount of CogniSync data required before model training/personalisation must be determined experimentally.
8. The academic workload scoring weights and thresholds are initial design parameters, not validated scientific constants.
9. The exact NLI checkpoint must be selected after model-card, licence and runtime review.
10. Newsela/WikiLarge are supporting simplification resources; a separate human-labelled meaning-checker evaluation set is required.
11. No stress or mood information will be collected or used.
12. The system remains useful without wearable data and without commute tracking.
13. The project does not claim causal effects from observational predictions.

---

# 19. References and data resources

## Project-provided datasets

- OULAD files supplied by the team: `assessments.csv`, `courses.csv`, `studentAssessment.csv`, `studentInfo.csv`, `studentRegistration.csv`, `vle.csv`, `OULAD.names`.
- Newsela simplification files supplied by the team: deletion, insertion and substitution JSON files.
- WikiLarge simplification files supplied by the team: deletion, insertion and substitution JSON files.

Dataset documentation and licences must be checked against the original providers before redistribution or public release.

## Google integration documentation

- Google Health developer documentation: https://developers.google.com/health
- Google Health setup: https://developers.google.com/health/setup
- Google Health endpoints: https://developers.google.com/health/endpoints
- Google Health data types: https://developers.google.com/health/data-types
- Google Health first API call guide: https://developers.google.com/health/codelabs/make-your-first-api-call

Verify current API documentation, eligibility, scopes, testing restrictions and terms at implementation time.

## Other technical references

- PyMuPDF documentation: https://pymupdf.readthedocs.io/
- scikit-learn documentation: https://scikit-learn.org/
- XGBoost documentation: https://xgboost.readthedocs.io/
- SHAP documentation: https://shap.readthedocs.io/
- Android geofencing documentation: https://developer.android.com/develop/sensors-and-location/location/geofencing
- Google Maps Routes API documentation: https://developers.google.com/maps/documentation/routes
- Hugging Face model documentation and model cards: https://huggingface.co/models

---

# 20. Final product definition

CogniSync is a personalised student learning-support prototype that:

1. Predicts a student's next quiz score and delayed topic-retention score as data becomes available.
2. Compares a previous-scores-only baseline with context-aware models using study, sleep/activity, academic workload and optional commute features.
3. Recommends suitable study windows using confirmed academic availability and predicted effectiveness.
4. Calculates transparent academic workload from timetables, exams, assignments and project deadlines.
5. Optionally imports consented sleep and activity records through Google Health API.
6. Optionally tracks configured home-college commute duration on Android and compares it with Google Maps expected duration.
7. Captures and confirms study activity within CogniSync.
8. Provides PDF-grounded summaries and quizzes.
9. Checks whether simplified explanations preserve source meaning using a pretrained NLI model and targeted factual checks.
10. Maintains clear privacy controls, data provenance, uncertainty and evaluation boundaries.

The initial ML research baseline is OULAD next-assessment score prediction. The principal deployed CogniSync prediction models are to be trained on CogniSync-collected quiz and delayed-quiz outcomes once enough high-quality, consented and correctly linked records exist. The system must never represent the OULAD benchmark as proof that the context-aware CogniSync model is already validated.
