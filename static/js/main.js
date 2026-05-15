/**
 * 药品管理系统 - 主JavaScript文件
 */

// 页面加载完成后执行
$(document).ready(function() {
    console.log('药品管理系统已加载');
    
    // 初始化工具提示
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // 初始化弹出框
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // 自动隐藏成功提示
    setTimeout(function() {
        $('.alert-success').fadeOut('slow');
    }, 3000);
});

/**
 * 标记预警为已读
 */
function markAlertAsRead(alertId) {
    $.ajax({
        url: `/alerts/${alertId}/read`,
        type: 'POST',
        success: function(response) {
            if (response.success) {
                $(`#alert-${alertId}`).removeClass('unread').addClass('read');
                $(`#alert-${alertId} .badge-unread`).remove();
            }
        },
        error: function(error) {
            console.error('标记已读失败:', error);
        }
    });
}

/**
 * 标记预警为已解决
 */
function resolveAlert(alertId) {
    if (!confirm('确认标记此预警为已解决？')) {
        return;
    }
    
    $.ajax({
        url: `/alerts/${alertId}/resolve`,
        type: 'POST',
        success: function(response) {
            if (response.success) {
                $(`#alert-${alertId}`).fadeOut('slow', function() {
                    $(this).remove();
                    // 检查是否还有其他预警
                    if ($('.alert-item').length === 0) {
                        location.reload();
                    }
                });
            }
        },
        error: function(error) {
            console.error('标记已解决失败:', error);
            alert('操作失败，请重试');
        }
    });
}

/**
 * 删除药品确认
 */
function confirmDelete(drugId, drugName) {
    if (confirm(`确认删除药品：${drugName}？\n\n此操作不可撤销！`)) {
        $(`#delete-form-${drugId}`).submit();
    }
}

/**
 * 快速入库
 */
function quickStockIn(drugId) {
    const quantity = prompt('请输入入库数量（片）：');
    
    if (quantity && !isNaN(quantity) && quantity > 0) {
        $.ajax({
            url: '/stocks/add',
            type: 'POST',
            data: {
                drug_id: drugId,
                quantity: quantity,
                notes: '快速入库'
            },
            success: function(response) {
                location.reload();
            },
            error: function(error) {
                alert('入库失败：' + error.responseJSON.message);
            }
        });
    }
}

/**
 * 筛选药品
 */
function filterDrugs() {
    const category = $('#category-filter').val();
    const stockStatus = $('#stock-status-filter').val();
    
    window.location.href = `/drugs?category=${category}&stock_status=${stockStatus}`;
}

/**
 * 导出数据到Excel
 */
function exportToExcel() {
    window.location.href = '/api/export/excel';
}

/**
 * 刷新统计信息
 */
function refreshStats() {
    $.ajax({
        url: '/api/stats',
        type: 'GET',
        success: function(data) {
            $('#total-drugs').text(data.total_drugs);
            $('#active-drugs').text(data.active_drugs);
            $('#alerts-count').text(data.alerts.total);
            $('#out-of-stock').text(data.out_of_stock);
        },
        error: function(error) {
            console.error('刷新统计失败:', error);
        }
    });
}

/**
 * 定时刷新（可选）
 */
setInterval(function() {
    // 每5分钟刷新一次统计信息
    // refreshStats();
}, 300000);

/**
 * 表单验证
 */
function validateDrugForm() {
    const name = $('#name').val().trim();
    const dailyDosage = parseFloat($('#daily_dosage').val());
    
    if (!name) {
        alert('请输入药品名称');
        return false;
    }
    
    if (dailyDosage < 0) {
        alert('每日用量不能为负数');
        return false;
    }
    
    return true;
}

/**
 * 计算到期日期
 */
function calculateExpiryDate() {
    const productionDate = $('#production_date').val();
    const validityPeriod = parseInt($('#validity_period').val());
    
    if (productionDate && validityPeriod > 0) {
        const prodDate = new Date(productionDate);
        const expiryDate = new Date(prodDate.setMonth(prodDate.getMonth() + validityPeriod));
        
        const year = expiryDate.getFullYear();
        const month = String(expiryDate.getMonth() + 1).padStart(2, '0');
        const day = String(expiryDate.getDate()).padStart(2, '0');
        
        $('#expiry_date').val(`${year}-${month}-${day}`);
    }
}

/**
 * 监听生产日期和有效期变化
 */
$(document).on('change', '#production_date, #validity_period', function() {
    calculateExpiryDate();
});

/**
 * 药品搜索功能
 */
function searchDrugs(keyword) {
    if (keyword.length < 2) {
        return;
    }
    
    $.ajax({
        url: `/api/drugs?search=${keyword}`,
        type: 'GET',
        success: function(data) {
            // 显示搜索结果
            console.log('搜索结果:', data);
        },
        error: function(error) {
            console.error('搜索失败:', error);
        }
    });
}

/**
 * 防抖函数
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * 监听搜索输入
 */
const searchInput = $('#search-input');
if (searchInput.length) {
    searchInput.on('input', debounce(function() {
        searchDrugs($(this).val());
    }, 300));
}
