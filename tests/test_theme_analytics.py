"""
Tests for theme analytics and reporting functionality
"""

import pytest
import json
from unittest.mock import Mock, patch
from app.services.unit_type_theme import UnitTypeThemeService
from app.models.unit_type_theme import UnitTypeTheme
from app.models.unit_type import UnitType
from app.services.base import ServiceException, ServiceNotFoundException


class TestThemeAnalytics:
    """Test theme analytics functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.theme_service = UnitTypeThemeService()
        
        # Mock themes
        self.theme1 = UnitTypeTheme(
            id=1,
            name="Executive Theme",
            description="Theme for executive units",
            primary_color="#0d6efd",
            secondary_color="#f8f9ff",
            text_color="#0d6efd",
            css_class_suffix="executive",
            display_label="Direzione",
            is_default=True,
            is_active=True
        )
        
        self.theme2 = UnitTypeTheme(
            id=2,
            name="Department Theme",
            description="Theme for department units",
            primary_color="#0dcaf0",
            secondary_color="#f0fdff",
            text_color="#0dcaf0",
            css_class_suffix="department",
            display_label="Dipartimento",
            is_default=False,
            is_active=True
        )
        
        self.theme3 = UnitTypeTheme(
            id=3,
            name="Unused Theme",
            description="Theme not used by any unit type",
            primary_color="#6c757d",
            secondary_color="#f8f9fa",
            text_color="#495057",
            css_class_suffix="unused",
            display_label="Non Utilizzato",
            is_default=False,
            is_active=True
        )

    @patch('app.services.unit_type_theme.UnitTypeThemeService.get_all')
    @patch('app.services.unit_type_theme.UnitTypeThemeService.db_manager')
    def test_get_theme_usage_statistics(self, mock_db, mock_get_all):
        """Test theme usage statistics calculation"""
        # Mock database response
        mock_db.fetch_all.return_value = [
            {
                'id': 1, 'name': 'Executive Theme', 'is_default': 1, 'is_active': 1,
                'usage_count': 5
            },
            {
                'id': 2, 'name': 'Department Theme', 'is_default': 0, 'is_active': 1,
                'usage_count': 3
            },
            {
                'id': 3, 'name': 'Unused Theme', 'is_default': 0, 'is_active': 1,
                'usage_count': 0
            }
        ]
        
        # Test usage statistics
        stats = self.theme_service.get_theme_usage_statistics()
        
        assert stats['total_themes'] == 3
        assert stats['total_usage'] == 8
        assert stats['unused_themes_count'] == 1
        assert stats['most_used_theme']['name'] == 'Executive Theme'
        assert stats['most_used_theme']['usage_count'] == 5
        assert stats['most_used_theme']['usage_percentage'] == 62.5

    @patch('app.services.unit_type_theme.UnitTypeThemeService.get_theme_usage_statistics')
    @patch('app.services.unit_type_theme.UnitTypeThemeService._get_theme_adoption_trends')
    @patch('app.services.unit_type_theme.UnitTypeThemeService._get_theme_performance_metrics')
    @patch('app.services.unit_type_theme.UnitTypeThemeService._get_theme_health_indicators')
    @patch('app.services.unit_type_theme.UnitTypeThemeService._generate_theme_recommendations')
    def test_get_theme_analytics_dashboard(self, mock_recommendations, mock_health, 
                                         mock_performance, mock_adoption, mock_usage_stats):
        """Test analytics dashboard data compilation"""
        # Mock return values
        mock_usage_stats.return_value = {
            'total_themes': 3,
            'active_themes': 3,
            'inactive_themes': 0,
            'total_usage': 8,
            'unused_themes_count': 1,
            'theme_distribution': [],
            'most_used_theme': {'name': 'Executive Theme', 'usage_count': 5},
            'least_used_theme': {'name': 'Department Theme', 'usage_count': 3}
        }
        
        mock_adoption.return_value = {
            'monthly_creation': [{'month': '2024-01', 'themes_created': 2}],
            'activation_status': {'active': 3, 'inactive': 0}
        }
        
        mock_performance.return_value = {
            'usage_metrics': {'average_usage': 2.67, 'max_usage': 5, 'min_usage': 0},
            'efficiency_metrics': {'utilization_rate': 66.7, 'unused_themes': 1}
        }
        
        mock_health.return_value = {
            'indicators': [],
            'overall_health': 'good'
        }
        
        mock_recommendations.return_value = [
            {
                'type': 'optimization',
                'priority': 'low',
                'title': 'Test Recommendation',
                'description': 'Test description'
            }
        ]
        
        # Test dashboard data
        dashboard_data = self.theme_service.get_theme_analytics_dashboard()
        
        assert 'overview' in dashboard_data
        assert 'usage_distribution' in dashboard_data
        assert 'adoption_trends' in dashboard_data
        assert 'performance_metrics' in dashboard_data
        assert 'health_indicators' in dashboard_data
        assert 'recommendations' in dashboard_data
        assert dashboard_data['overview']['total_themes'] == 3
        assert dashboard_data['overview']['active_themes'] == 3

    @patch('app.services.unit_type_theme.UnitTypeThemeService.db_manager')
    def test_get_theme_adoption_trends(self, mock_db):
        """Test theme adoption trends calculation"""
        # Mock database responses
        mock_db.fetch_all.side_effect = [
            # Monthly creation data
            [
                {'month': '2024-01', 'themes_created': 2},
                {'month': '2024-02', 'themes_created': 1}
            ],
            # Activation status data
            [
                {'is_active': 1, 'count': 3},
                {'is_active': 0, 'count': 0}
            ]
        ]
        
        trends = self.theme_service._get_theme_adoption_trends()
        
        assert 'monthly_creation' in trends
        assert 'activation_status' in trends
        assert len(trends['monthly_creation']) == 2
        assert trends['activation_status']['active'] == 3

    @patch('app.services.unit_type_theme.UnitTypeThemeService.db_manager')
    def test_get_theme_performance_metrics(self, mock_db):
        """Test theme performance metrics calculation"""
        # Mock database responses
        mock_db.fetch_one.side_effect = [
            # Usage metrics
            {'avg_usage': 2.67, 'max_usage': 5, 'min_usage': 0},
            # Efficiency metrics
            {'total_themes': 3, 'used_themes': 2}
        ]
        
        metrics = self.theme_service._get_theme_performance_metrics()
        
        assert 'usage_metrics' in metrics
        assert 'efficiency_metrics' in metrics
        assert metrics['usage_metrics']['average_usage'] == 2.67
        assert metrics['efficiency_metrics']['utilization_rate'] == 66.7

    @patch('app.services.unit_type_theme.UnitTypeThemeService.get_all')
    @patch('app.services.unit_type_theme.UnitTypeThemeService.db_manager')
    def test_get_theme_health_indicators(self, mock_db, mock_get_all):
        """Test theme health indicators"""
        # Mock themes with validation issues
        invalid_theme = UnitTypeTheme(
            id=4,
            name="Invalid Theme",
            primary_color="invalid_color",  # Invalid color
            css_class_suffix="invalid",
            display_label="Invalid"
        )
        
        mock_get_all.return_value = [self.theme1, self.theme2, invalid_theme]
        
        # Mock database response for inactive themes in use
        mock_db.fetch_all.return_value = []
        
        health = self.theme_service._get_theme_health_indicators()
        
        assert 'indicators' in health
        assert 'overall_health' in health
        # Should detect validation issues
        assert len(health['indicators']) > 0

    def test_generate_theme_recommendations(self):
        """Test theme recommendations generation"""
        # Test with high unused themes count
        theme_stats = {
            'unused_themes_count': 5,
            'active_themes': 2,
            'total_themes': 10,
            'most_used_theme': {
                'name': 'Executive Theme',
                'usage_percentage': 85
            }
        }
        
        recommendations = self.theme_service._generate_theme_recommendations(theme_stats)
        
        assert len(recommendations) > 0
        # Should recommend cleanup of unused themes
        cleanup_rec = next((r for r in recommendations if 'Consolida' in r['title']), None)
        assert cleanup_rec is not None
        assert cleanup_rec['priority'] == 'medium'

    @patch('app.services.unit_type_theme.UnitTypeThemeService.get_by_id')
    @patch('app.services.unit_type_theme.UnitTypeThemeService.get_unit_types_using_theme')
    def test_get_theme_impact_analysis(self, mock_get_unit_types, mock_get_by_id):
        """Test theme impact analysis"""
        # Mock theme
        mock_get_by_id.return_value = self.theme1
        
        # Mock unit types using theme
        mock_get_unit_types.return_value = [
            {
                'id': 1,
                'name': 'Executive Unit',
                'short_name': 'EXEC',
                'level': 1,
                'units_count': 25
            },
            {
                'id': 2,
                'name': 'Department Unit',
                'short_name': 'DEPT',
                'level': 2,
                'units_count': 10
            }
        ]
        
        impact = self.theme_service.get_theme_impact_analysis(1)
        
        assert impact['theme']['id'] == 1
        assert impact['total_units_affected'] == 35
        assert len(impact['affected_unit_types']) == 2
        assert impact['impact_severity'] == 'high'  # > 10 units
        assert len(impact['warnings']) > 0  # Should have warnings for high impact

    @patch('app.services.unit_type_theme.UnitTypeThemeService.get_by_id')
    def test_get_theme_impact_analysis_not_found(self, mock_get_by_id):
        """Test impact analysis for non-existent theme"""
        mock_get_by_id.return_value = None
        
        with pytest.raises(ServiceNotFoundException):
            self.theme_service.get_theme_impact_analysis(999)

    def test_generate_impact_recommendations(self):
        """Test impact recommendations generation"""
        theme = self.theme1
        unit_types = [
            {'id': 1, 'name': 'Unit 1', 'units_count': 25},
            {'id': 2, 'name': 'Unit 2', 'units_count': 15}
        ]
        
        # Test critical severity (default theme)
        recommendations = self.theme_service._generate_impact_recommendations(
            theme, unit_types, 'critical'
        )
        
        assert len(recommendations) > 0
        # Should recommend testing and backup for critical changes
        test_rec = next((r for r in recommendations if 'Testa' in r), None)
        assert test_rec is not None

    @patch('app.services.unit_type_theme.UnitTypeThemeService.db_manager')
    def test_get_most_least_used_themes_report(self, mock_db):
        """Test detailed usage report generation"""
        # Mock database response
        mock_db.fetch_all.return_value = [
            {
                'id': 1, 'name': 'Executive Theme', 'description': 'Executive theme',
                'is_default': 1, 'is_active': 1, 'usage_count': 5,
                'total_units_count': 25, 'unit_type_names': 'Executive,Director',
                'datetime_created': '2024-01-01 10:00:00',
                'datetime_updated': '2024-01-15 14:30:00'
            },
            {
                'id': 2, 'name': 'Department Theme', 'description': 'Department theme',
                'is_default': 0, 'is_active': 1, 'usage_count': 3,
                'total_units_count': 15, 'unit_type_names': 'Department',
                'datetime_created': '2024-01-02 11:00:00',
                'datetime_updated': '2024-01-16 15:30:00'
            },
            {
                'id': 3, 'name': 'Unused Theme', 'description': 'Unused theme',
                'is_default': 0, 'is_active': 1, 'usage_count': 0,
                'total_units_count': 0, 'unit_type_names': None,
                'datetime_created': '2024-01-03 12:00:00',
                'datetime_updated': '2024-01-17 16:30:00'
            }
        ]
        
        report = self.theme_service.get_most_least_used_themes_report()
        
        assert 'summary' in report
        assert 'most_used_themes' in report
        assert 'least_used_themes' in report
        assert 'unused_themes' in report
        assert 'all_themes_data' in report
        
        assert report['summary']['total_themes'] == 3
        assert report['summary']['used_themes'] == 2
        assert report['summary']['unused_themes'] == 1
        assert len(report['most_used_themes']) == 2
        assert len(report['unused_themes']) == 1


class TestThemeAnalyticsRoutes:
    """Test theme analytics routes"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)

    @patch('app.routes.themes.UnitTypeThemeService')
    def test_theme_analytics_dashboard_route(self, mock_service_class, client):
        """Test analytics dashboard route"""
        # Mock service
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        mock_dashboard_data = {
            'overview': {
                'total_themes': 3,
                'active_themes': 3,
                'inactive_themes': 0,
                'total_usage': 8,
                'unused_themes_count': 1
            },
            'usage_distribution': [],
            'most_used_theme': {'name': 'Executive Theme'},
            'least_used_theme': {'name': 'Department Theme'},
            'adoption_trends': {'monthly_creation': []},
            'performance_metrics': {'usage_metrics': {}, 'efficiency_metrics': {}},
            'health_indicators': {'indicators': [], 'overall_health': 'good'},
            'recommendations': []
        }
        
        mock_service.get_theme_analytics_dashboard.return_value = mock_dashboard_data
        
        response = client.get("/themes/analytics/dashboard")
        
        assert response.status_code == 200
        assert "Dashboard Analisi Temi" in response.text
        mock_service.get_theme_analytics_dashboard.assert_called_once()

    @patch('app.routes.themes.UnitTypeThemeService')
    def test_theme_usage_report_route(self, mock_service_class, client):
        """Test usage report route"""
        # Mock service
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        mock_usage_report = {
            'summary': {
                'total_themes': 3,
                'used_themes': 2,
                'unused_themes': 1,
                'total_usage': 8
            },
            'most_used_themes': [],
            'least_used_themes': [],
            'unused_themes': [],
            'all_themes_data': []
        }
        
        mock_service.get_most_least_used_themes_report.return_value = mock_usage_report
        
        response = client.get("/themes/analytics/usage-report")
        
        assert response.status_code == 200
        assert "Report Utilizzo Temi" in response.text
        mock_service.get_most_least_used_themes_report.assert_called_once()

    @patch('app.routes.themes.UnitTypeThemeService')
    def test_theme_impact_analysis_route(self, mock_service_class, client):
        """Test impact analysis route"""
        # Mock service
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        mock_impact_analysis = {
            'theme': {'id': 1, 'name': 'Executive Theme', 'is_default': True},
            'affected_unit_types': [],
            'total_units_affected': 25,
            'levels_affected': [1, 2],
            'impact_severity': 'high',
            'warnings': ['High impact warning'],
            'css_impact': {
                'cache_invalidation_required': True,
                'estimated_regeneration_time': 'medium',
                'affected_css_classes': ['unit-executive']
            },
            'recommendations': ['Test changes carefully']
        }
        
        mock_service.get_theme_impact_analysis.return_value = mock_impact_analysis
        
        response = client.get("/themes/1/impact-analysis")
        
        assert response.status_code == 200
        assert "Analisi Impatto" in response.text
        mock_service.get_theme_impact_analysis.assert_called_once_with(1)

    @patch('app.routes.themes.UnitTypeThemeService')
    def test_dashboard_analytics_api(self, mock_service_class, client):
        """Test dashboard analytics API endpoint"""
        # Mock service
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        mock_dashboard_data = {
            'overview': {'total_themes': 3},
            'usage_distribution': [],
            'recommendations': []
        }
        
        mock_service.get_theme_analytics_dashboard.return_value = mock_dashboard_data
        
        response = client.get("/themes/api/analytics/dashboard-data")
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'data' in data
        mock_service.get_theme_analytics_dashboard.assert_called_once()

    @patch('app.routes.themes.UnitTypeThemeService')
    def test_usage_statistics_api(self, mock_service_class, client):
        """Test usage statistics API endpoint"""
        # Mock service
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        mock_usage_stats = {
            'total_themes': 3,
            'active_themes': 3,
            'total_usage': 8
        }
        
        mock_service.get_theme_usage_statistics.return_value = mock_usage_stats
        
        response = client.get("/themes/api/analytics/usage-stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data']['total_themes'] == 3
        mock_service.get_theme_usage_statistics.assert_called_once()

    @patch('app.routes.themes.UnitTypeThemeService')
    def test_theme_impact_api(self, mock_service_class, client):
        """Test theme impact API endpoint"""
        # Mock service
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        mock_impact_analysis = {
            'theme': {'id': 1, 'name': 'Executive Theme'},
            'impact_severity': 'high',
            'total_units_affected': 25
        }
        
        mock_service.get_theme_impact_analysis.return_value = mock_impact_analysis
        
        response = client.get("/themes/api/analytics/1/impact")
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['data']['impact_severity'] == 'high'
        mock_service.get_theme_impact_analysis.assert_called_once_with(1)


class TestThemeAnalyticsIntegration:
    """Integration tests for theme analytics"""

    @pytest.fixture
    def setup_test_data(self):
        """Set up test data for integration tests"""
        # This would set up actual test database data
        # For now, we'll mock it
        pass

    def test_analytics_data_consistency(self, setup_test_data):
        """Test that analytics data is consistent across different methods"""
        # This would test that usage statistics match between different
        # analytics methods when using real data
        pass

    def test_performance_with_large_dataset(self, setup_test_data):
        """Test analytics performance with large datasets"""
        # This would test performance with many themes and unit types
        pass

    def test_analytics_caching(self, setup_test_data):
        """Test that analytics data is properly cached"""
        # This would test caching mechanisms for analytics data
        pass


if __name__ == "__main__":
    pytest.main([__file__])