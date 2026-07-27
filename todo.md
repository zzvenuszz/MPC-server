# Refactor MCP Server thành Plugin Framework

Hãy refactor MCP Server hiện tại (entry point là `server.py`) thành một **Plugin Framework** có khả năng mở rộng lâu dài.

## Mục tiêu

* Giữ nguyên chức năng hiện có.
* Không tạo project mới, chỉ refactor project hiện tại.
* Không làm thay đổi giao thức MCP.
* Giữ tương thích với các MCP Client như Cline, Claude Desktop, ChatGPT...
* Sau khi hoàn thành, việc thêm một tool mới không cần sửa `server.py` hoặc mã nguồn lõi.

## Kiến trúc mong muốn

Thiết kế hệ thống theo các thành phần:

* Plugin Loader
* Plugin Registry
* Plugin Manager
* Compatibility Layer (Adapter)
* Provider (nguồn plugin)
* Dashboard API
* CLI quản lý plugin

Áp dụng các nguyên tắc SOLID, Open/Closed và Separation of Concerns.

## Plugin System

Mỗi plugin là một module độc lập.

Plugin phải có metadata (manifest) mô tả:

* id
* tên
* phiên bản
* mô tả
* tác giả
* loại plugin
* danh sách tool
* dependencies
* permissions
* trạng thái

Plugin Loader phải tự động phát hiện plugin thông qua metadata, không được hardcode tên hoặc import từng plugin.

## Refactor các Tool hiện có

Hiện tại các tool đang được đăng ký trực tiếp trong mã nguồn.

Yêu cầu:

* Chuyển toàn bộ tool hiện có thành plugin độc lập.
* Giữ nguyên tên, tham số và hành vi.
* Chỉ xóa phần hardcode sau khi plugin mới hoạt động chính xác.
* Không được làm mất bất kỳ chức năng nào.

## Khả năng mở rộng

Framework cần hỗ trợ nhiều loại plugin:

* Python Plugin
* Knowledge Plugin
* API Plugin
* Workflow Plugin

Đồng thời chuẩn bị sẵn kiến trúc để sau này có thể hỗ trợ:

* Plugin Marketplace
* Cài plugin từ GitHub
* Cài plugin từ ZIP
* Plugin Update
* Plugin Versioning
* Plugin Dependency
* Plugin Permission
* Plugin Settings
* Hot Reload

Không cần triển khai đầy đủ các tính năng trên, nhưng kiến trúc phải hỗ trợ.

## Tương thích hệ sinh thái MCP

Ưu tiên tương thích với:

* MCP Specification chính thức
* MCP Python SDK
* FastMCP
* Các MCP Tool phổ biến trên GitHub

Không tạo một chuẩn plugin đóng khiến plugin cộng đồng không thể sử dụng.

Nếu cần khác biệt, hãy xây dựng Adapter/Compatibility Layer thay vì sửa plugin gốc.

## Plugin Lifecycle

Thiết kế vòng đời plugin đầy đủ:

* Load
* Enable
* Disable
* Reload
* Shutdown

Mỗi plugin có context riêng, logger riêng, storage riêng và cấu hình riêng.

## Quản lý Plugin

Framework cần có khả năng:

* Load plugin tự động
* Reload plugin
* Enable/Disable plugin
* Kiểm tra tính hợp lệ
* Quản lý dependency
* Quản lý permission
* Ghi log riêng cho từng plugin

Plugin lỗi không được làm sập toàn bộ MCP Server.

## CLI và Dashboard

Chuẩn bị backend để sau này có thể xây Dashboard và CLI quản lý plugin.

Ví dụ:

* Danh sách plugin
* Thông tin plugin
* Reload
* Enable
* Disable
* Validate
* Logs
* Settings

## Chất lượng mã nguồn

* Không hardcode.
* Có type hints và docstring.
* Chia module rõ ràng.
* Dễ test.
* Dễ bảo trì.
* Dễ mở rộng.

## Quan trọng

Ưu tiên một kiến trúc sạch và có khả năng phát triển lâu dài hơn là hoàn thành nhanh.

Nếu trong quá trình refactor có điểm nào có thể cải thiện kiến trúc, hãy chủ động đề xuất và triển khai theo hướng tốt hơn, miễn vẫn giữ tương thích với hệ thống hiện tại và chuẩn MCP.
