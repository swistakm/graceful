# -*- coding: utf-8 -*-
import falcon


class DeleteMixin(object):
    def delete(self, **kwargs):
        raise NotImplementedError("delete method not implemented")

    def on_delete(self, req, resp, **kwargs):
        self.delete(**kwargs)
        resp.status = falcon.HTTP_NO_CONTENT


class UpdateMixin(object):
    def update(self, validated_data, **kwargs):
        raise NotImplementedError("update method not implemented")

    def on_put(self, req, resp, **kwargs):
        self.update(self.validate_data(req, partial=False), **kwargs)
        resp.status = falcon.HTTP_NO_CONTENT


class CreateMixin(object):
    def create(self, validated_data, **kwargs):
        raise NotImplementedError("create method not implemented")

    def on_post(self, req, resp, **kwargs):
        location = self.create(
            self.validate_data(req, partial=False), **kwargs
        )

        if location:
            resp.location = location

        resp.status = falcon.HTTP_CREATED

