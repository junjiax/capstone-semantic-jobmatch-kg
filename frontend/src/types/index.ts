export type UserRole = "applicant" | "admin" | "hr";

export interface User {
  id: number;
  email: string;
  fullName?: string;
  role: UserRole;
  isActive: boolean;
}

export interface SkillItem {
  id?: number;
  name: string;
  similarity?: number;
  weight?: number;
  importance?: number;
  expertise?: string;
  domain?: string;
}

export interface SkillGapData {
  jobTitle?: string;
  totalRequiredSkills: number;
  totalMatchedSkills: number;
  totalMissingSkills: number;
  skillCoverageRatio: number;
  matchedSkills: SkillItem[];
  partiallyMatchedSkills?: SkillItem[];
  missingSkills: SkillItem[];
  extraSkills?: SkillItem[];
  explanation?: string;
  recommendation?: string;
}

export interface MatchScores {
  totalResult: number;
  skillScore: number;
  domainScore: number;
  expertiseScore: number;
  experienceScore: number;
  qualificationScore: number;
}

// BÀI TOÁN 1: So khớp 1 CV vs 1 JD
export interface MatchResultResponse {
  cvId: number;
  jdId: number;
  jobTitle: string;
  totalResult: number;
  isSuitable: boolean;
  scores: MatchScores;
  skillGap: SkillGapData;
  explanation: string;
}

// BÀI TOÁN 3: Hybrid Candidate Search cho HR
export interface CandidateSearchResult {
  cvId: number;
  candidateTitle?: string;
  totalScore: number;
  vectorScore: number;
  graphSkillScore: number;
  matchedSkillsCount: number;
  requiredSkillsCount: number;
  matchedSkills: Array<string | { name?: string; importance?: number }>;
  missingSkills: Array<string | { name?: string; importance?: number }>;
  experienceYears?: number;
}

// KNOWLEDGE GRAPH
export interface GraphNode {
  id: string;
  label: string;
  type: "Domain" | "Expertise" | "Skill" | "JobPosition" | "Candidate";
  properties?: Record<string, unknown>;
}

export interface GraphLink {
  source: string;
  target: string;
  relationship: "IN_DOMAIN" | "IN_EXPERTISE" | "REQUIRE" | "HAS_SKILL" | "RELATED_TO" | "MATCHES_JD";
}

export interface GraphSyncStats {
  users: number;
  skills: number;
  jobs: number;
  cvs: number;
  domains: number;
  expertises: number;
  educations: number;
  work_experiences: number;
}
