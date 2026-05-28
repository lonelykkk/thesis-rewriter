/**
 * 论文降重降AI助手 - 前端交互逻辑
 */
(function () {
    "use strict";

    // =============================================
    //  页面路由
    // =============================================
    var path = window.location.pathname;
    if (path === "/" || path === "") {
        initIndexPage();
    }
    if (path === "/compare") {
        initResultPage();
    }

    // =============================================
    //  首页初始化
    // =============================================
    function initIndexPage() {
        var inputText = safeEl("inputText");
        var charCount = safeEl("charCount");
        var rewriteBtn = safeEl("rewriteBtn");
        var btnContent = safeEl("btnContent");
        var clearBtn = safeEl("clearBtn");
        var loadingOverlay = safeEl("loadingOverlay");
        var modeRadios = document.querySelectorAll('input[name="mode"]');
        var exampleBtns = document.querySelectorAll(".example-btn");

        if (!inputText || !rewriteBtn) {
            console.warn("[论文助手] 关键DOM元素未找到，跳过初始化");
            return;
        }

        // 示例文本
        var EXAMPLES = {
            abstract: [
                "本文以深度学习技术为基础，提出了一种基于卷积神经网络的新型图像分类方法。",
                "该方法通过对传统网络结构进行改进，引入了注意力机制和多尺度特征融合策略，",
                "显著提升了模型在复杂场景下的分类准确率。实验结果表明，该方法在多个公开数据集上",
                "均取得了优于现有方法的性能，Top-1准确率提升了3.2个百分点。本研究为图像分类任务",
                "提供了一种新的解决思路，具有重要的理论意义和应用价值。"
            ].join("\n"),
            intro: [
                "近年来，随着大数据技术的快速发展和计算能力的显著提升，深度学习在计算机视觉领域",
                "取得了突破性进展。图像分类作为计算机视觉的核心任务之一，在自动驾驶、医疗影像诊断、",
                "智能安防等领域具有广泛的应用前景。然而，现有的图像分类方法在处理复杂场景时仍面临",
                "诸多挑战，如光照变化、遮挡、视角变化等问题严重影响模型的分类性能。因此，研究一种",
                "鲁棒性更强、准确率更高的图像分类方法具有重要的理论意义和实际应用价值。"
            ].join("\n"),
            method: [
                "本研究采用定量分析与定性分析相结合的研究方法。首先，通过文献研究法系统梳理了",
                "国内外相关研究成果，总结了现有方法的优缺点。其次，采用实验研究法，在标准数据集上",
                "对提出的方法进行了全面的性能评估。最后，运用统计分析方法对实验数据进行了深入分析，",
                "验证了方法的有效性和优越性。研究过程中严格控制了实验变量，保证了研究结果的可靠性。"
            ].join("\n"),
            conclusion: [
                "本文针对图像分类任务中存在的问题，提出了一种基于注意力机制和多尺度特征融合的",
                "新型深度学习方法。通过在多个公开数据集上的实验验证，证明该方法在分类准确率、",
                "模型鲁棒性和泛化能力方面均优于现有主流方法。本研究的主要贡献在于：（1）设计了",
                "一种轻量级的注意力模块，有效增强了模型对关键特征的提取能力；（2）提出了多尺度",
                "特征融合策略，充分利用了不同层次的特征信息。未来的工作将致力于将该方法应用于",
                "更广泛的计算机视觉任务中，进一步提升其实用价值。"
            ].join("\n"),
        };

        // 加载历史记录
        loadHistory(inputText);

        // === 字数统计 ===
        if (inputText && charCount) {
            inputText.addEventListener("input", function () {
                var len = inputText.value.length;
                charCount.textContent = len + " / 50000 字";
                charCount.className = len > 45000
                    ? "text-xs text-red-400 font-medium"
                    : len > 30000
                        ? "text-xs text-yellow-400"
                        : "text-xs text-gray-400";
            });
        }

        // === 清空按钮 ===
        if (clearBtn) {
            clearBtn.addEventListener("click", function () {
                inputText.value = "";
                if (charCount) charCount.textContent = "0 / 50000 字";
                inputText.focus();
            });
        }

        // === 示例文本 ===
        for (var ei = 0; ei < exampleBtns.length; ei++) {
            (function (btn) {
                btn.addEventListener("click", function () {
                    var key = this.dataset.example;
                    if (EXAMPLES[key]) {
                        inputText.value = EXAMPLES[key];
                        if (charCount) {
                            charCount.textContent = inputText.value.length + " / 50000 字";
                        }
                        inputText.focus();
                    }
                });
            })(exampleBtns[ei]);
        }

        // === 主处理函数 ===
        async function handleRewrite() {
            var text = inputText.value.trim();
            if (!text) {
                inputText.classList.add("border-red-400");
                setTimeout(function () { inputText.classList.remove("border-red-400"); }, 800);
                showToast("请先输入论文内容", "warning");
                inputText.focus();
                return;
            }
            if (text.length < 20) {
                showToast("文本过短，建议输入至少20字", "warning");
                return;
            }

            var mode = "both";
            for (var mi = 0; mi < modeRadios.length; mi++) {
                if (modeRadios[mi].checked) {
                    mode = modeRadios[mi].value;
                    break;
                }
            }

            rewriteBtn.disabled = true;
            rewriteBtn.classList.add("opacity-60", "cursor-not-allowed");
            btnContent.innerHTML = "<span>处理中...</span>";
            if (loadingOverlay) {
                loadingOverlay.classList.remove("hidden");
                loadingOverlay.classList.add("flex");
            }

            try {
                var response = await fetch("/rewrite", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ text: text, mode: mode }),
                });
                var data = await response.json();

                if (data.success) {
                    // ===== 🐛 Bug 修复 =====
                    // 旧代码：通过 URL 参数传递所有数据（original/rewritten/changes JSON）
                    // 问题：changes JSON 较大时 URL 被截断或编码错误，导致改动详情不显示
                    // 修复：直接使用 record_id 跳转，服务器从数据库加载完整数据
                    // ========================
                    window.location.href = "/compare?record_id=" + data.record_id;
                } else {
                    showToast(data.error || "处理失败，请重试", "error");
                }
            } catch (err) {
                showToast("网络错误，请确保服务器已启动", "error");
                console.error("[论文助手] 请求失败:", err);
            } finally {
                rewriteBtn.disabled = false;
                rewriteBtn.classList.remove("opacity-60", "cursor-not-allowed");
                btnContent.innerHTML = [
                    '<svg class="w-5 h-5 inline-block mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">',
                    '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>',
                    '</svg><span>开始处理</span>'
                ].join("");
                if (loadingOverlay) {
                    loadingOverlay.classList.add("hidden");
                    loadingOverlay.classList.remove("flex");
                }
            }
        }

        rewriteBtn.addEventListener("click", handleRewrite);
        inputText.addEventListener("keydown", function (e) {
            if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
                e.preventDefault();
                handleRewrite();
            }
        });

        // === 移动端历史弹窗 ===
        var mobileBtn = safeEl("mobileHistoryBtn");
        var mobilePanel = safeEl("mobileHistoryPanel");
        var mobileOverlay = safeEl("mobileHistoryOverlay");
        var mobileClose = safeEl("mobileHistoryClose");
        if (mobileBtn && mobilePanel) {
            mobileBtn.addEventListener("click", function () {
                mobilePanel.classList.remove("hidden");
                loadMobileHistory(inputText);
            });
            if (mobileOverlay) {
                mobileOverlay.addEventListener("click", function () {
                    mobilePanel.classList.add("hidden");
                });
            }
            if (mobileClose) {
                mobileClose.addEventListener("click", function () {
                    mobilePanel.classList.add("hidden");
                });
            }
        }

        console.log("[论文助手] 首页初始化完成 | 提示: Ctrl+Enter 快速提交");
    }

    // =============================================
    //  加载历史记录（桌面侧边栏）
    // =============================================
    function loadHistory(inputText) {
        var listEl = document.getElementById("historyList");
        var countEl = document.getElementById("historyCount");
        if (!listEl) return;

        fetch("/api/history")
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (!data.success || !data.records || data.records.length === 0) {
                    listEl.innerHTML = '<div class="p-6 text-center text-sm text-gray-400"><p>暂无历史记录</p></div>';
                    if (countEl) countEl.textContent = "0";
                    return;
                }
                if (countEl) countEl.textContent = data.total;
                listEl.innerHTML = renderHistoryItems(data.records, inputText);
            })
            .catch(function (err) {
                listEl.innerHTML = '<div class="p-6 text-center text-sm text-red-400"><p>加载失败</p></div>';
                console.error("[论文助手] 加载历史失败:", err);
            });
    }

    // =============================================
    //  加载历史记录（移动端弹窗）
    // =============================================
    function loadMobileHistory(inputText) {
        var listEl = document.getElementById("mobileHistoryList");
        if (!listEl) return;

        listEl.innerHTML = '<div class="p-6 text-center text-sm text-gray-400"><p>加载中...</p></div>';

        fetch("/api/history")
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (!data.success || !data.records || data.records.length === 0) {
                    listEl.innerHTML = '<div class="p-6 text-center text-sm text-gray-400"><p>暂无历史记录</p></div>';
                    return;
                }
                listEl.innerHTML = renderHistoryItems(data.records, inputText, true);
            })
            .catch(function () {
                listEl.innerHTML = '<div class="p-6 text-center text-sm text-red-400"><p>加载失败</p></div>';
            });
    }

    // =============================================
    //  渲染历史记录条目
    // =============================================
    function renderHistoryItems(records, inputText, isMobile) {
        var modeLabels = {
            both: "全面优化",
            reduce: "仅降重",
            deai: "仅降AI",
        };
        var modeColors = {
            both: "bg-blue-100 text-blue-700",
            reduce: "bg-green-100 text-green-700",
            deai: "bg-purple-100 text-purple-700",
        };

        return records.map(function (rec) {
            var label = modeLabels[rec.mode] || rec.mode;
            var color = modeColors[rec.mode] || "bg-gray-100 text-gray-700";
            var title = rec.title || rec.preview || "未命名";

            return [
                '<div class="history-item px-3 py-2.5 hover:bg-gray-50 cursor-pointer transition-colors group border-b border-gray-50 last:border-b-0" data-id="' + rec.id + '">',
                '  <div class="flex items-center justify-between mb-0.5">',
                '    <span class="text-xs font-medium px-1.5 py-0.5 rounded ' + color + '">' + label + '</span>',
                '    <div class="flex items-center gap-1">',
                '      <span class="text-xs text-gray-400">' + rec.created_at + '</span>',
                '    </div>',
                '  </div>',
                '  <div class="flex items-center justify-between gap-1">',
                '    <div class="history-title flex-1 min-w-0 text-sm font-medium text-gray-700 truncate" title="' + escapeHtml(title) + '">' + escapeHtml(title) + '</div>',
                '    <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">',
                '      <button class="rename-history text-gray-300 hover:text-blue-500 transition-colors p-0.5" data-id="' + rec.id + '" data-title="' + escapeHtml(title) + '">',
                '        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/></svg>',
                '      </button>',
                '      <button class="delete-history text-gray-300 hover:text-red-500 transition-colors p-0.5" data-id="' + rec.id + '">',
                '        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>',
                '      </button>',
                '    </div>',
                '  </div>',
                '</div>'
            ].join("");
        }).join("");
    }

    // =============================================
    //  重命名历史记录（内联编辑）
    // =============================================
    function startRename(recordId, titleEl) {
        var currentTitle = titleEl.textContent;
        var input = document.createElement("input");
        input.type = "text";
        input.value = currentTitle;
        input.className = "w-full text-sm font-medium text-gray-700 bg-blue-50 border border-blue-300 rounded px-1.5 py-0.5 focus:outline-none focus:ring-1 focus:ring-blue-400";
        input.maxLength = 100;
        titleEl.replaceWith(input);
        input.focus();
        input.select();

        function saveRename() {
            var newTitle = input.value.trim();
            if (!newTitle || newTitle === currentTitle) {
                cancelRename(input, titleEl, currentTitle);
                return;
            }
            fetch("/api/history/" + recordId + "/rename", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ title: newTitle }),
            })
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    if (data.success) {
                        var newDiv = document.createElement("div");
                        newDiv.className = titleEl.className;
                        newDiv.title = newTitle;
                        newDiv.textContent = newTitle;
                        input.replaceWith(newDiv);
                        showToast("已重命名", "success");
                        // 刷新历史列表以同步标题
                        var inputEl = document.getElementById("inputText");
                        loadHistory(inputEl);
                        loadMobileHistory(inputEl);
                    } else {
                        showToast(data.error || "重命名失败", "error");
                        cancelRename(input, titleEl, currentTitle);
                    }
                })
                .catch(function () {
                    showToast("网络错误", "error");
                    cancelRename(input, titleEl, currentTitle);
                });
        }

        function cancelRename(inp, originalEl, fallbackText) {
            var div = document.createElement("div");
            div.className = originalEl.className;
            div.title = fallbackText;
            div.textContent = fallbackText;
            inp.replaceWith(div);
        }

        input.addEventListener("keydown", function (ev) {
            if (ev.key === "Enter") {
                ev.preventDefault();
                input.blur();
            } else if (ev.key === "Escape") {
                ev.preventDefault();
                cancelRename(input, titleEl, currentTitle);
            }
        });
        input.addEventListener("blur", saveRename);
    }

    // =============================================
    //  绑定历史记录事件（委托）
    // =============================================
    document.addEventListener("click", function (e) {
        // 点击重命名按钮
        var renameBtn = e.target.closest(".rename-history");
        if (renameBtn) {
            e.stopPropagation();
            var recordId = renameBtn.dataset.id;
            var item = renameBtn.closest(".history-item");
            var titleEl = item ? item.querySelector(".history-title") : null;
            if (recordId && titleEl) {
                startRename(recordId, titleEl);
            }
            return;
        }

        // 点击记录条目 - 跳转到对比页
        var item = e.target.closest(".history-item");
        if (item && !e.target.closest(".delete-history")) {
            var recordId = item.dataset.id;
            if (recordId) {
                window.location.href = "/compare?record_id=" + recordId;
            }
            return;
        }

        // 点击删除按钮
        var delBtn = e.target.closest(".delete-history");
        if (delBtn) {
            e.stopPropagation();
            var delId = delBtn.dataset.id;
            if (delId && confirm("确定删除这条历史记录吗？")) {
                fetch("/api/history/" + delId, { method: "DELETE" })
                    .then(function (r) { return r.json(); })
                    .then(function (data) {
                        if (data.success) {
                            showToast("已删除", "success");
                            var inputEl = document.getElementById("inputText");
                            loadHistory(inputEl);
                            loadMobileHistory(inputEl);
                        } else {
                            showToast("删除失败", "error");
                        }
                    })
                    .catch(function () {
                        showToast("网络错误", "error");
                    });
            }
        }
    });

    // =============================================
    //  结果页初始化
    // =============================================
    function initResultPage() {
        var original = "";
        var rewritten = "";
        var changesStr = "{}";

        // 优先从 RECORD_DATA（服务器端渲染）加载
        if (typeof RECORD_DATA !== "undefined") {
            original = RECORD_DATA.original || "";
            rewritten = RECORD_DATA.rewritten || "";
            changesStr = (typeof RECORD_DATA.changes === "string")
                ? RECORD_DATA.changes
                : JSON.stringify(RECORD_DATA.changes);
        } else {
            // 后备：从 URL 参数加载
            var params = new URLSearchParams(window.location.search);
            original = params.get("original") || "";
            rewritten = params.get("rewritten") || "";
            changesStr = params.get("changes") || "{}";
        }

        var originalEl = document.getElementById("originalText");
        var rewrittenEl = document.getElementById("rewrittenText");

        // 如果 pre 元素没有内容（从 URL 参数来的），设置内容
        if (originalEl && !originalEl.textContent.trim()) {
            originalEl.textContent = original;
        }
        if (rewrittenEl && !rewrittenEl.textContent.trim()) {
            rewrittenEl.textContent = rewritten;
        }

        // 改动统计
        try {
            var changesData = (typeof changesStr === "string")
                ? JSON.parse(changesStr)
                : changesStr;
            var total = changesData.total || 0;
            var countEl = document.getElementById("changeCount");
            if (countEl) {
                if (typeof total === "number") {
                    countEl.textContent = total + " 处改动";
                } else {
                    countEl.textContent = "AI 处理 - " + total;
                }
            }

            var list = document.getElementById("changesList");
            if (list) {
                var details = changesData.details || [];
                if (details.length > 0) {
                    renderChanges(list, details);
                } else {
                    list.innerHTML = '<div class="p-6 text-center text-gray-400"><p>AI处理模式 - 请直接在文本中查看改动</p></div>';
                }
            }
        } catch (e) {
            console.warn("[论文助手] 解析改动详情失败:", e);
        }

        // 复制按钮
        var copyBtn = document.getElementById("copyResultBtn");
        if (copyBtn) {
            copyBtn.addEventListener("click", function () {
                navigator.clipboard.writeText(rewritten).then(function () {
                    showToast("已复制到剪贴板", "success");
                }).catch(function () {
                    var ta = document.createElement("textarea");
                    ta.value = rewritten;
                    document.body.appendChild(ta);
                    ta.select();
                    document.execCommand("copy");
                    document.body.removeChild(ta);
                    showToast("已复制到剪贴板", "success");
                });
            });
        }

        // 导出按钮
        var exportBtn = document.getElementById("exportBtn");
        if (exportBtn) {
            exportBtn.addEventListener("click", function () {
                var blob = new Blob([rewritten], { type: "text/plain;charset=utf-8" });
                var url = URL.createObjectURL(blob);
                var a = document.createElement("a");
                a.href = url;
                a.download = "论文改写结果_" + new Date().toISOString().slice(0, 10) + ".txt";
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                showToast("导出成功", "success");
            });
        }

        console.log("[论文助手] 结果页初始化完成");
    }

    // =============================================
    //  渲染改动详情
    // =============================================
    function renderChanges(list, details) {
        var typeLabels = {
            synonym: "同义词替换",
            transformation: "句式变换",
            word_adjust: "词语调整",
            humanize_transition: "添加过渡词",
            humanize_order: "语序调整",
            humanize_perspective: "添加视角",
            humanize_other: "人性化处理",
        };

        list.innerHTML = details.map(function (item, idx) {
            var label = typeLabels[item.type] || item.type;
            return [
                '<div class="p-4 hover:bg-gray-50 transition-colors border-b border-gray-100">',
                '  <div class="flex items-start gap-3">',
                '    <span class="inline-flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-600 text-xs font-medium flex-shrink-0">',
                (idx + 1).toString(),
                '    </span>',
                '    <div class="flex-1 min-w-0">',
                '      <span class="text-xs font-medium px-2 py-0.5 rounded bg-blue-100 text-blue-700">' + label + '</span>',
                '      <div class="text-sm text-gray-500 mt-1">',
                '        <span class="text-red-400 line-through">' + escapeHtml(item.original) + '</span>',
                '        <span class="text-gray-300 mx-1">→</span>',
                '        <span class="text-green-600">' + escapeHtml(item.modified) + '</span>',
                '      </div>',
                '    </div>',
                '  </div>',
                '</div>'
            ].join("");
        }).join("");
    }

    // =============================================
    //  工具函数
    // =============================================
    function safeEl(id) {
        var el = document.getElementById(id);
        if (!el) {
            console.warn("[论文助手] 元素 #" + id + " 未找到");
        }
        return el;
    }

    function escapeHtml(str) {
        var div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    function showToast(message, type) {
        var existing = document.querySelector(".custom-toast");
        if (existing) existing.remove();

        var bgColor = "bg-gray-800";
        if (type === "success") bgColor = "bg-green-600";
        else if (type === "warning") bgColor = "bg-yellow-500";
        else if (type === "error") bgColor = "bg-red-500";

        var toast = document.createElement("div");
        toast.className = "custom-toast fixed top-20 right-4 z-[9999] " + bgColor +
            " text-white px-5 py-3 rounded-xl shadow-lg text-sm font-medium";
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(function () {
            toast.style.opacity = "0";
            toast.style.transition = "opacity 0.3s";
            setTimeout(function () { toast.remove(); }, 300);
        }, 3000);
    }
})();
