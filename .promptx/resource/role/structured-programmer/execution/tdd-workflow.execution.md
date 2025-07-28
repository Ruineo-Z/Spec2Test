<execution>
  <constraint>
    ## TDD技术约束
    - **测试框架限制**：必须选择项目技术栈兼容的测试框架
    - **测试环境要求**：需要独立的测试环境，避免污染生产数据
    - **CI/CD集成**：测试必须能够在持续集成环境中自动运行
    - **覆盖率要求**：代码覆盖率应达到80%以上
    - **性能约束**：单元测试执行时间不应超过几秒钟
  </constraint>

  <rule>
    ## TDD强制执行规则
    - **测试先行强制**：任何产品代码都必须先有失败的测试
    - **最小实现原则**：只编写刚好让测试通过的代码
    - **重构安全网**：重构前必须确保所有测试通过
    - **一次一个测试**：每次只编写一个测试用例
    - **快速反馈循环**：红→绿→重构循环应在几分钟内完成
    - **测试独立性**：每个测试用例必须独立运行
  </rule>

  <guideline>
    ## TDD指导原则
    - **从简单开始**：优先编写最简单的测试用例
    - **边界条件重视**：特别关注边界值和异常情况
    - **可读性优先**：测试代码的可读性比产品代码更重要
    - **重构勇气**：在测试保护下大胆重构代码
    - **持续改进**：根据测试反馈持续改进设计
  </guideline>

  <process>
    ## TDD三步循环详细流程
    
    ### 🔴 Red阶段：编写失败测试
    
    ```mermaid
    flowchart TD
        A[理解需求] --> B[设计测试用例]
        B --> C[编写测试代码]
        C --> D[运行测试]
        D --> E{测试失败?}
        E -->|是| F[确认测试正确性]
        E -->|否| G[检查测试逻辑]
        G --> C
        F --> H[进入Green阶段]
    ```
    
    **Red阶段检查清单**：
    - [ ] 测试用例清晰描述了期望行为
    - [ ] 测试确实失败了（红色状态）
    - [ ] 失败原因是因为功能未实现，而非测试错误
    - [ ] 测试代码本身是正确的
    
    **常见测试模式**：
    ```python
    # 1. 基础功能测试
    def test_function_returns_expected_value():
        # Given
        input_data = "test_input"
        expected = "expected_output"
        
        # When
        result = target_function(input_data)
        
        # Then
        assert result == expected
    
    # 2. 异常情况测试
    def test_function_raises_exception_for_invalid_input():
        with pytest.raises(ValueError):
            target_function(invalid_input)
    
    # 3. 边界条件测试
    def test_function_handles_edge_cases():
        assert target_function("") == ""
        assert target_function(None) is None
    ```
    
    ### 🟢 Green阶段：最小实现
    
    ```mermaid
    flowchart TD
        A[分析失败测试] --> B[设计最小实现]
        B --> C[编写产品代码]
        C --> D[运行所有测试]
        D --> E{所有测试通过?}
        E -->|是| F[进入Refactor阶段]
        E -->|否| G[修复代码]
        G --> D
    ```
    
    **Green阶段原则**：
    - **最小可行实现**：只写让测试通过的最少代码
    - **硬编码优先**：初期可以使用硬编码值
    - **重复代码允许**：这个阶段允许代码重复
    - **性能忽略**：暂时不考虑性能优化
    
    **实现策略**：
    ```python
    # 第一次实现：硬编码
    def calculate_total(items):
        return 100  # 硬编码让测试通过
    
    # 第二次实现：简单逻辑
    def calculate_total(items):
        if not items:
            return 0
        return sum(item.price for item in items)
    
    # 第三次实现：处理更多情况
    def calculate_total(items):
        if not items:
            return 0
        total = 0
        for item in items:
            if item.price > 0:
                total += item.price
        return total
    ```
    
    ### 🔄 Refactor阶段：重构优化
    
    ```mermaid
    flowchart TD
        A[识别代码异味] --> B[设计重构方案]
        B --> C[执行重构]
        C --> D[运行所有测试]
        D --> E{测试仍然通过?}
        E -->|是| F[评估是否需要继续重构]
        E -->|否| G[回滚重构]
        G --> B
        F --> H{需要继续?}
        H -->|是| A
        H -->|否| I[完成当前循环]
    ```
    
    **重构目标**：
    - **消除重复代码**：DRY原则（Don't Repeat Yourself）
    - **提高可读性**：清晰的命名和结构
    - **简化复杂度**：降低圈复杂度
    - **改善设计**：应用设计模式和原则
    
    **常见重构技巧**：
    ```python
    # 重构前：重复代码
    def process_user_data(user):
        if user.age >= 18:
            user.status = "adult"
            user.permissions = ["read", "write"]
        else:
            user.status = "minor"
            user.permissions = ["read"]
    
    # 重构后：提取方法
    def process_user_data(user):
        user.status = determine_status(user.age)
        user.permissions = get_permissions(user.status)
    
    def determine_status(age):
        return "adult" if age >= 18 else "minor"
    
    def get_permissions(status):
        return ["read", "write"] if status == "adult" else ["read"]
    ```
    
    ## 任务级TDD实施流程
    
    ### 任务开始前
    ```mermaid
    graph TD
        A[选择当前任务] --> B[理解任务需求]
        B --> C[设计测试策略]
        C --> D[准备测试环境]
        D --> E[开始第一个测试]
    ```
    
    ### 任务执行中
    ```mermaid
    graph LR
        A[🔴 写测试] --> B[🟢 写实现]
        B --> C[🔄 重构]
        C --> D{任务完成?}
        D -->|否| A
        D -->|是| E[任务验收]
    ```
    
    ### 任务完成后
    ```mermaid
    graph TD
        A[运行完整测试套件] --> B[检查代码覆盖率]
        B --> C[代码审查]
        C --> D[更新文档]
        D --> E[提交代码]
        E --> F[更新ToDoList]
    ```
  </process>

  <criteria>
    ## TDD质量评价标准

    ### 测试质量指标
    - ✅ **覆盖率达标**：代码覆盖率 ≥ 80%
    - ✅ **测试独立性**：每个测试可以独立运行
    - ✅ **测试速度**：单元测试执行时间 < 5秒
    - ✅ **测试可读性**：测试意图清晰明确
    
    ### 代码质量指标
    - ✅ **功能正确性**：所有测试通过
    - ✅ **代码简洁性**：没有重复代码
    - ✅ **设计合理性**：符合SOLID原则
    - ✅ **可维护性**：易于理解和修改
    
    ### 流程执行指标
    - ✅ **循环完整性**：严格遵循红→绿→重构
    - ✅ **步骤规范性**：每个步骤都有明确产出
    - ✅ **反馈及时性**：快速发现和修复问题
    - ✅ **持续改进**：根据反馈优化流程
    
    ### 任务管理指标
    - ✅ **任务完整性**：每个任务都有明确的完成标准
    - ✅ **进度可控性**：任务进度透明可追踪
    - ✅ **质量一致性**：每个任务都达到相同的质量标准
    - ✅ **交付及时性**：按预估时间完成任务
  </criteria>
</execution>