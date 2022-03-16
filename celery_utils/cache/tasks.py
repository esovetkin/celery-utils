import os
import time

from celery_utils.decorators.jobs \
    import task_decorator

from celery_utils.storage.remotestorage_path \
    import RemoteStoragePath, is_remote_path

from celery_utils.utils.files \
    import move_file


# TODO call_fn_cache: retry on any exceptions?
#       - retry on storage errors?
@task_decorator(cache = None,
                get_args_locally = False)
def call_fn_cache(result, ofn, storage_type):
    if result is None:
        return ofn

    ofn = RemoteStoragePath\
        (ofn, remotetype = storage_type)
    result_rmt = RemoteStoragePath\
        (result, remotetype = storage_type)

    if os.path.exists(result_rmt.path):
        move_file(result_rmt.path, ofn.path, True)

    if is_remote_path(result):
        ofn.link(result_rmt.path)
        return str(ofn)

    ofn.upload()
    return str(ofn)
