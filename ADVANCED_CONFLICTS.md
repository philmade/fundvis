# Advanced Conflict of Interest (CoI) Representation & Detection

This document outlines conceptual ideas for enhancing the representation, detection, and exploration of Conflicts of Interest (CoIs) in a research context, building upon a network graph of authors, institutions, funders, and papers.

## 1. Defining Conflicts of Interest (CoI)

A Conflict of Interest in research occurs when an individual's private interests (such as financial gain, career advancement, or personal relationships) could improperly influence, or be perceived to improperly influence, their professional judgments or actions.

### Types/Levels of CoI:

*   **Direct Financial Ties:**
    *   **Funding Recipient:** An author or institution directly receiving funding (grants, salary support, consultancy fees, honoraria, travel reimbursement) from an entity (e.g., a Funder in our model) that may have an interest in the research outcomes.
    *   **Equity/Ownership:** An author holding shares, stock options, or ownership in a company whose products are studied or that could be affected by the research.
    *   **Employment/Consultancy:** An author being employed by, or serving as a paid consultant/advisor to, an entity with an interest in the research.
    *   **Patents/Royalties:** An author holding patents or expecting royalties related to the research subject.
*   **Institutional Affiliations & Conflicts:**
    *   **Institutional Funding:** An institution receiving significant funding from an entity that could influence research conducted at that institution, even if specific authors are not directly funded.
    *   **Institutional Leadership Roles:** An author holding a leadership position within their institution that has a vested interest in specific research outcomes or collaborations.
*   **Reviewer & Editorial Conflicts:**
    *   **Recent Collaboration:** A reviewer or editor having recently collaborated (e.g., co-authored a paper, co-investigator on a grant) with an author of a manuscript under review.
    *   **Shared Affiliation:** A reviewer or editor being from the same institution as an author.
    *   **Competitive Relationship:** A reviewer or editor being a direct competitor (e.g., working on very similar research, competing for the same grants).
    *   **Financial Ties to Author's Funder:** A reviewer having financial ties to a funder of the author's research.
*   **Interpersonal Relationships:**
    *   Family members, close personal relationships. (Harder to model systematically without explicit input).
*   **Intellectual Conflicts:**
    *   Strongly held beliefs or theoretical commitments that might prevent objective evaluation. (Very hard to model).

### Operationalizing Definitions (Data Patterns):

*   **Direct Financial (Author-Funder):**
    *   Pattern: `Author <-[FundedBy]-> Funder` AND `Author <-[Published]-> Paper` AND `Paper <-[RelevantToTopicOf]-> Funder's Interest`.
    *   The link `Author <-[FundedBy]-> Funder` is represented by our `AuthorFunders` association object linking an Author, Funder, and a Paper.
*   **Direct Financial (Author-Company for Product Study):**
    *   Pattern: `Author <-[ReceivesPayment/OwnsEquityIn]-> Company` AND `Paper <-[StudiesProductOf]-> Company`. (Requires Company nodes and product data).
*   **Institutional Affiliation Conflict:**
    *   Pattern: `Author <-[AffiliatedWith]-> Institution` AND `Institution <-[ReceivesSignificantFundingFrom]-> Funder` AND `Paper <-[PublishedByAuthorAt]-> Institution` AND `Paper <-[RelevantToTopicOf]-> Funder's Interest`.
*   **Reviewer Conflict (Collaboration):**
    *   Pattern: `Reviewer <-[CoAuthoredPaperWithInXTime]-> AuthorOfSubmission` OR `Reviewer <-[CoInvestigatorOnGrantWith]-> AuthorOfSubmission`.
*   **Reviewer Conflict (Shared Institution):**
    *   Pattern: `Reviewer <-[AffiliatedWith]-> Institution` AND `AuthorOfSubmission <-[AffiliatedWith]-> Institution`.

## 2. Enhanced Data Requirements

To move beyond basic affiliation/funding links and detect more nuanced CoIs, richer data is needed:

*   **Nature of Funding/Relationship:**
    *   For Author-Funder links: Grant, consultancy, honorarium, travel grant, salary support, equity.
    *   For Institution-Funder links: Unrestricted grant, research grant, philanthropic donation, sponsored research agreement.
*   **Role of Individuals:**
    *   On Papers: Principal Investigator (PI), Co-Investigator, Corresponding Author, Contributor.
    *   On Grants: PI, Co-PI.
    *   Professional Role: Consultant, Advisory Board Member, Employee (and role type).
*   **Specific Timeframes:**
    *   Start and end dates for affiliations, funding periods, consultancies, employment. This is crucial for determining relevance (e.g., funding active during research vs. funding received 10 years prior).
*   **Monetary Value/Significance:**
    *   Approximate value of grants, consultancy fees, equity (e.g., thresholds for "significant"). Often sensitive and hard to obtain.
*   **Topics/Keywords:**
    *   For Papers: Detailed keywords, MeSH terms.
    *   For Grants: Purpose, keywords.
    *   For Funders/Companies: Areas of interest, products, services.
*   **Conflict of Interest Disclosures:**
    *   Structured data from author CoI disclosure forms submitted to journals or institutions.
*   **Reviewer Identity (for editorial systems):**
    *   Names of reviewers assigned to papers (kept confidential within the system).

### Potential Data Sources:

*   **Expanded API Queries:**
    *   OpenAlex: Can provide grant information (funder, sometimes PI), author affiliations with history.
    *   PubMed/EuropePMC: Author affiliations, grant IDs (linkable to funders via other APIs like Crossref).
    *   Crossref: Funder information, grant details, ORCID links.
    *   ORCID: Author's employment, funding, works (if user populates their record thoroughly).
*   **User Input / Curated Datasets:**
    *   Direct input from authors/institutions to declare relationships and their nature/timeframes.
    *   Integration with institutional research management systems.
    *   Journal platforms for reviewer CoI checks.
*   **Specialized CoI Databases:** (e.g., ProPublica's Dollars for Docs, OpenPayments in the US for healthcare).
*   **Company Databases:** (e.g., Crunchbase, financial news APIs for company interests and executive roles).

## 3. Advanced Visualization & Interaction Techniques

### Visual Cues:

*   **Edge Styling for CoIs:**
    *   **Color:** Red or orange edges for direct, high-risk CoIs (e.g., author funded by company whose drug they are testing). Yellow for moderate/indirect.
    *   **Thickness/Weight:** Thicker edges for more significant relationships (e.g., larger grant, direct employment).
    *   **Dashing/Pattern:** Dashed lines for historical relationships, dotted for potential/unconfirmed.
*   **Node Overlays/Icons:**
    *   A small warning icon (e.g., ⚠️) on nodes directly involved in a potential CoI relevant to a selected paper or context.
    *   Color-coding the border of a node if it's involved in a CoI.
*   **Highlighting Paths:** When a CoI is identified, highlight the full path of nodes and edges that constitute the conflict.

### CoI Scoring/Severity:

*   **Rule-Based Scoring:** Assign scores based on CoI type (e.g., direct financial tie = high score, shared institution for reviewer = lower score).
*   **Weighting Factors:** Incorporate weights for:
    *   Recency of relationship.
    *   Magnitude of financial interest (if known).
    *   Role of the individual (e.g., PI on a grant has higher weight than a consultant).
*   **Categorization:** Instead of a numeric score, categorize CoIs (e.g., "High Financial CoI," "Institutional CoI," "Potential Reviewer CoI").
*   **Transparency:** The system should be able to explain *why* a certain score or category was assigned.

### Temporal Analysis:

*   **Timeline Visualization:** For a selected author or paper, display a timeline showing:
    *   Publication dates.
    *   Funding periods (start/end).
    *   Affiliation periods.
    *   Consultancy periods.
    This allows visual inspection of overlaps that might constitute CoIs.
*   **Filtering by Time:** Allow users to filter the network to show only relationships active within a specific date range.

### Interactive Exploration:

*   **Dedicated CoI View/Mode:** A toggle that re-styles the graph to emphasize CoI-relevant connections and hide non-relevant data.
*   **"Explain This Conflict" Feature:** Right-clicking a highlighted CoI edge or node could bring up a panel detailing:
    *   The nature of the relationship.
    *   The data source for the link.
    *   The timeframe.
    *   The rule that triggered the CoI flag.
*   **Drill-Down on Nodes:** Clicking a Funder node could show its areas of interest, other funded authors/papers. Clicking an Author could show all their disclosed CoIs.
*   **Sensitivity Sliders:** Allow users to adjust thresholds for what constitutes a "significant" CoI (e.g., minimum funding amount, recency).

### Contextual Information:

*   **Linking to Policies:** For identified CoIs, provide links to relevant institutional, journal, or governmental CoI policies.
*   **News/Database Links:** Link Funder/Company nodes to news articles about their activities or databases like OpenPayments or RetractionWatch for further context.
*   **User Annotation:** Allow users (e.g., administrators, reviewers) to annotate potential CoIs with notes, confirm/dismiss flags, or add missing information.

## 4. Workflow for Identifying and Reviewing Conflicts

A potential user workflow for leveraging these advanced features:

1.  **Initial Data Ingestion:**
    *   A paper (DOI) is entered, or an author profile is the starting point.
    *   Data is pulled from OpenAlex and other configured sources.
    *   The base network graph is constructed.
2.  **Automated CoI Flagging:**
    *   The system applies predefined rules (based on operationalized definitions) to the graph.
    *   Potential CoIs are flagged, scored, or categorized.
    *   Visual cues (colors, icons) are applied to the graph.
3.  **User Review & Exploration (e.g., by an editor, ethics committee, or researcher themselves):**
    *   **Overview:** User views the graph with CoI highlights. A dashboard might summarize potential CoIs (e.g., "3 High Financial CoIs, 5 Reviewer Conflicts").
    *   **Filtering:** User filters by paper, author, funder, or CoI type/severity.
    *   **Drill-Down:** User selects a flagged node or edge.
        *   The sidebar (or a modal) displays detailed information about the entities involved.
        *   The "Explain This Conflict" feature provides rationale.
        *   Temporal views are accessed if relevant.
    *   **Contextual Lookup:** User accesses linked policies, external databases, or news for more context.
4.  **Decision & Action:**
    *   **Reviewer Assignment:** If checking for reviewer CoIs, the system helps select appropriate, non-conflicted reviewers.
    *   **Disclosure Verification:** For a published paper, check if identified potential CoIs were appropriately disclosed by authors.
    *   **Investigation:** For serious potential CoIs, initiate further investigation.
5.  **Annotation & Record Keeping:**
    *   User annotates findings, confirms or dismisses flagged CoIs within the system.
    *   A report of potential and reviewed CoIs can be generated.

This advanced system aims to provide a more comprehensive and insightful tool for managing the complexities of conflicts of interest in research.
