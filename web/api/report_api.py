"""
报告相关API模块
"""
from typing import Dict, Any
from utils.logger import logger
from database import db
from ai.report_generator import report_generator
from utils.validators import (
    validate_generate_report_params,
    validate_get_reports_params,
    validate_get_report_detail_params,
    validate_delete_report_params,
    validate_get_latest_report_params,
    GenerateReportParams,
    GetReportsParams,
    GetReportDetailParams,
    DeleteReportParams,
    GetLatestReportParams
)


class ReportAPI:
    """报告API处理器"""
    
    @validate_generate_report_params
    def generate_report(self, handler, params: GenerateReportParams):
        """生成报告（手动触发）"""
        try:
            report_type = params.report_type
            hours = params.hours
            
            logger.info(f"开始生成{report_type}报告，时间范围：{hours}小时")
            
            # 生成报告
            result = report_generator.generate_report(report_type, hours)
            
            if result['success']:
                handler._send_json_response({
                    'success': True,
                    'message': '报告生成成功',
                    'report_id': result['report_id'],
                    'report_title': result['report_title'],
                    'news_count': result['news_count'],
                    'generation_time': result['generation_time']
                })
            else:
                handler._send_error_response(result.get('error', '报告生成失败'))
                
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            handler._send_error_response(str(e))
    
    @validate_get_reports_params
    def get_reports(self, handler, params: GetReportsParams):
        """获取报告列表"""
        try:
            report_type = params.type
            limit = params.limit
            offset = params.offset
            
            # 获取报告列表
            reports = db.get_reports_by_type(report_type, limit, offset)
            
            handler._send_json_response({
                'success': True,
                'data': reports,
                'count': len(reports),
                'type': report_type,
                'limit': limit,
                'offset': offset
            })
            
        except Exception as e:
            logger.error(f"获取报告列表失败: {e}")
            handler._send_error_response(str(e))
    
    @validate_get_report_detail_params
    def get_report_detail(self, handler, params: GetReportDetailParams):
        """获取报告详情"""
        try:
            report_id = params.id
            
            # 获取报告详情
            report = db.get_report_by_id(report_id)
            
            if not report:
                handler._send_error_response("报告不存在")
                return
            
            # 解析报告内容
            try:
                import json
                content = json.loads(report['content'])
                report['content'] = content
            except json.JSONDecodeError:
                logger.error(f"报告内容解析失败: {report_id}")
                report['content'] = None
            
            handler._send_json_response({
                'success': True,
                'data': report
            })
            
        except Exception as e:
            logger.error(f"获取报告详情失败: {e}")
            handler._send_error_response(str(e))
    
    @validate_delete_report_params
    def delete_report(self, handler, params: DeleteReportParams):
        """删除报告"""
        try:
            report_id = params.id
            
            # 删除报告
            success = db.delete_report(report_id)
            
            if success:
                handler._send_json_response({
                    'success': True,
                    'message': '报告删除成功'
                })
            else:
                handler._send_error_response("报告删除失败")
                
        except Exception as e:
            logger.error(f"删除报告失败: {e}")
            handler._send_error_response(str(e))
    
    @validate_get_latest_report_params
    def get_latest_report(self, handler, params: GetLatestReportParams):
        """获取最新报告"""
        try:
            report_type = params.type
            
            # 获取最新报告
            report = db.get_latest_report(report_type)
            
            if not report:
                handler._send_json_response({
                    'success': True,
                    'data': None
                })
                return
            
            # 解析报告内容
            try:
                import json
                content = json.loads(report['content'])
                report['content'] = content
            except json.JSONDecodeError:
                logger.error(f"报告内容解析失败: {report['id']}")
                report['content'] = None
            
            handler._send_json_response({
                'success': True,
                'data': report
            })
            
        except Exception as e:
            logger.error(f"获取最新报告失败: {e}")
            handler._send_error_response(str(e))


report_api = ReportAPI()