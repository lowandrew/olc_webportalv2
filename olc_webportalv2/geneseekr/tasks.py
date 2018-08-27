from background_task import background


@background(schedule=1)
def run_geneseekr(geneseekr_request_pk):
    print('Running GeneSeekr')
