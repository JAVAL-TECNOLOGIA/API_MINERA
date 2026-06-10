from mssql.base import (
    CursorWrapper as MssqlCursorWrapper,
    Database,
    DatabaseWrapper as MssqlDatabaseWrapper,
)


class CursorWrapper(MssqlCursorWrapper):
    def _inline_none_params(self, sql, params):
        if params is None or None not in params or not isinstance(sql, str):
            return sql, params

        marker = "%s"
        parts = sql.split(marker)
        if len(parts) - 1 != len(params):
            return sql, params

        new_sql = [parts[0]]
        new_params = []
        for value, tail in zip(params, parts[1:]):
            if value is None:
                new_sql.append("NULL")
            else:
                new_sql.append(marker)
                new_params.append(value)
            new_sql.append(tail)

        return "".join(new_sql), tuple(new_params)

    def execute(self, sql, params=None):
        self.last_sql = sql
        if "GROUP BY" in sql:
            sql, params = self.format_group_by_params(sql, params)
        if params is not None and params != []:
            sql, params = self._inline_none_params(sql, params)
        sql = self.format_sql(sql, params)
        params = self.format_params(params)
        self.last_params = params
        try:
            return self.cursor.execute(sql, params)
        except Database.Error as exc:
            self.connection._on_error(exc)
            raise

    def executemany(self, sql, params_list=()):
        if not params_list:
            return None

        raw_sql = sql
        raw_params = list(params_list)
        sql, first_params = self._inline_none_params(raw_sql, raw_params[0])
        none_mask = tuple(value is None for value in raw_params[0])
        normalized_params = [first_params]

        for params in raw_params[1:]:
            if tuple(value is None for value in params) != none_mask:
                return super().executemany(raw_sql, params_list)
            _, normalized = self._inline_none_params(raw_sql, params)
            normalized_params.append(normalized)

        sql = self.format_sql(sql, normalized_params[0])
        normalized_params = [self.format_params(params) for params in normalized_params]
        try:
            return self.cursor.executemany(sql, normalized_params)
        except Database.Error as exc:
            self.connection._on_error(exc)
            raise


class DatabaseWrapper(MssqlDatabaseWrapper):
    sql_server_version = MssqlDatabaseWrapper.sql_server_version
    to_azure_sql_db = MssqlDatabaseWrapper.to_azure_sql_db

    def create_cursor(self, name=None):
        return CursorWrapper(self.connection.cursor(), self)
