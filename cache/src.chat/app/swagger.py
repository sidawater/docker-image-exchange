from starlette.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html


def register_swagger_routes(app, static_path: str, base_url: str):
    app.mount(
        base_url + '/static',
        StaticFiles(directory=static_path),
        name="static"
    )

    async def _load_docs():
        return get_swagger_ui_html(
            openapi_url=base_url + '/openapi.json',
            title="API Docs",
            swagger_js_url=base_url + "/static/swagger-ui-bundle.js",
            swagger_css_url=base_url + "/static/swagger-ui.css",
        )
    app.router.add_api_route(
        base_url + '/docs',
        _load_docs,
        methods=['GET'],
        summary="swagger docs",
        description="",
    )
    app.router.add_api_route(
        base_url,
        lambda : 'ok',
        methods=['GET'],
        summary="health check",
        description="",
    )
    app.mount(
        base_url + '/static',
        StaticFiles(directory=static_path),
        name="static"
    )
