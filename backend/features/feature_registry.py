# backend/features/feature_registry.py
from typing import Dict, Any, NamedTuple

class FeatureDefinition(NamedTuple):
    name: str
    entity_type: str
    feature_version: int
    lower_bound: float
    upper_bound: float
    default_value: float
    is_target: int  # 0 or 1

FEATURE_REGISTRY: Dict[str, FeatureDefinition] = {
    # Case Features
    "victim_count": FeatureDefinition("victim_count", "case", 1, 0.0, 10.0, 1.0, 0),
    "accused_count": FeatureDefinition("accused_count", "case", 1, 0.0, 50.0, 1.0, 0),
    "act_count": FeatureDefinition("act_count", "case", 1, 0.0, 10.0, 1.0, 0),
    "section_count": FeatureDefinition("section_count", "case", 1, 0.0, 50.0, 1.0, 0),
    "severity_score": FeatureDefinition("severity_score", "case", 1, 1.0, 10.0, 1.0, 0),
    "gravity_score": FeatureDefinition("gravity_score", "case", 1, 0.0, 1.0, 0.0, 0),
    "investigation_age": FeatureDefinition("investigation_age", "case", 1, 0.0, 2000.0, 0.0, 0),
    "arrest_delay": FeatureDefinition("arrest_delay", "case", 1, -1.0, 1000.0, -1.0, 0), # -1 means no arrest
    "court_delay": FeatureDefinition("court_delay", "case", 1, 0.0, 2000.0, 180.0, 0),
    "hotspot_distance": FeatureDefinition("hotspot_distance", "case", 1, 0.0, 100.0, 99.0, 0),
    "district_crime_rate": FeatureDefinition("district_crime_rate", "case", 1, 0.0, 10000.0, 0.0, 0),
    "crime_frequency": FeatureDefinition("crime_frequency", "case", 1, 0.0, 2000.0, 0.0, 0),
    "weekly_incident_rate": FeatureDefinition("weekly_incident_rate", "case", 1, 0.0, 1000.0, 0.0, 0),
    "monthly_trend": FeatureDefinition("monthly_trend", "case", 1, 0.0, 10.0, 1.0, 0),
    "seasonality_score": FeatureDefinition("seasonality_score", "case", 1, 0.0, 2.0, 1.0, 0),
    # Case Targets
    "chargesheet_delay_target": FeatureDefinition("chargesheet_delay_target", "case", 1, -1.0, 2000.0, -1.0, 1),
    "priority_target": FeatureDefinition("priority_target", "case", 1, 0.0, 100.0, 10.0, 1),

    # Suspect Features
    "prior_case_count": FeatureDefinition("prior_case_count", "suspect", 1, 0.0, 500.0, 0.0, 0),
    "repeat_offender_count": FeatureDefinition("repeat_offender_count", "suspect", 1, 0.0, 500.0, 0.0, 0),
    "community_score": FeatureDefinition("community_score", "suspect", 1, -1.0, 1000.0, -1.0, 0),
    "community_size": FeatureDefinition("community_size", "suspect", 1, 0.0, 10000.0, 0.0, 0),
    "pagerank_score": FeatureDefinition("pagerank_score", "suspect", 1, 0.0, 1.0, 0.0, 0),
    "betweenness_score": FeatureDefinition("betweenness_score", "suspect", 1, 0.0, 1.0, 0.0, 0),
    "degree_centrality": FeatureDefinition("degree_centrality", "suspect", 1, 0.0, 1.0, 0.0, 0),
    "closeness": FeatureDefinition("closeness", "suspect", 1, 0.0, 1.0, 0.0, 0),
    "component_id": FeatureDefinition("component_id", "suspect", 1, -1.0, 1000.0, -1.0, 0),
    "bridge_score": FeatureDefinition("bridge_score", "suspect", 1, 0.0, 10.0, 0.0, 0),
    "gang_score": FeatureDefinition("gang_score", "suspect", 1, 0.0, 1.0, 0.0, 0),
    "risk_factor_score": FeatureDefinition("risk_factor_score", "suspect", 1, 0.0, 200.0, 0.0, 0),
    "organized_crime_score": FeatureDefinition("organized_crime_score", "suspect", 1, 0.0, 1.0, 0.0, 0),
    "centrality_rank": FeatureDefinition("centrality_rank", "suspect", 1, 1.0, 100000.0, 99999.0, 0),
    # Suspect Targets
    "repeat_offender_target": FeatureDefinition("repeat_offender_target", "suspect", 1, 0.0, 1.0, 0.0, 1),

    # Officer Features
    "active_cases": FeatureDefinition("active_cases", "officer", 1, 0.0, 500.0, 0.0, 0),
    "closed_cases": FeatureDefinition("closed_cases", "officer", 1, 0.0, 2000.0, 0.0, 0),
    "average_chargesheet_delay": FeatureDefinition("average_chargesheet_delay", "officer", 1, -1.0, 1000.0, -1.0, 0),
    "average_investigation_duration": FeatureDefinition("average_investigation_duration", "officer", 1, -1.0, 1000.0, -1.0, 0),
    "officer_load": FeatureDefinition("officer_load", "officer", 1, 0.0, 10.0, 1.0, 0),
    "clearance_rate": FeatureDefinition("clearance_rate", "officer", 1, 0.0, 1.0, 0.0, 0),
    "case_backlog": FeatureDefinition("case_backlog", "officer", 1, 0.0, 500.0, 0.0, 0),
    "risk_case_ratio": FeatureDefinition("risk_case_ratio", "officer", 1, 0.0, 1.0, 0.0, 0),

    # Hotspot Features
    "cluster_size": FeatureDefinition("cluster_size", "hotspot", 1, 0.0, 10000.0, 0.0, 0),
    "crime_density": FeatureDefinition("crime_density", "hotspot", 1, 0.0, 1000.0, 0.0, 0),
    "cluster_risk": FeatureDefinition("cluster_risk", "hotspot", 1, 0.0, 1000.0, 0.0, 0),
    "repeat_offender_density": FeatureDefinition("repeat_offender_density", "hotspot", 1, 0.0, 1.0, 0.0, 0),
    "severity_density": FeatureDefinition("severity_density", "hotspot", 1, 1.0, 10.0, 1.0, 0),
    "historical_baseline": FeatureDefinition("historical_baseline", "hotspot", 1, 0.0, 1000.0, 0.0, 0),
    "weekly_change": FeatureDefinition("weekly_change", "hotspot", 1, -100.0, 1000.0, 0.0, 0),
    "weekly_growth": FeatureDefinition("weekly_growth", "hotspot", 1, -1000.0, 1000.0, 0.0, 0),
    "emerging_cluster": FeatureDefinition("emerging_cluster", "hotspot", 1, 0.0, 1.0, 0.0, 0),
    # Hotspot Targets
    "future_cluster_size": FeatureDefinition("future_cluster_size", "hotspot", 1, 0.0, 10000.0, 0.0, 1),
    "hotspot_growth_target": FeatureDefinition("hotspot_growth_target", "hotspot", 1, -1000.0, 1000.0, 0.0, 1),
}
