from aida.common.extendeddicts import DefaultFieldsAttributeDict, Enumerate

class CalcState(Enumerate):
    pass

calcStates = CalcState((
        'UNDETERMINED',
        'NEW', # just created
        'SUBMITTING', # being submitted to cluster
        'WITHSCHEDULER', # on the scheduler (on any unfinished status:
                         # QUEUED, QUEUED_HELD, SUSPENDED, RUNNING)
        'FINISHED',   # Calculation finished on scheduler, not yet retrieved
                      # (both DONE and FAILED)
        'RETRIEVING', # while retrieving data
        'RETRIEVED',  # data retrieved, no more need to connect to scheduler
        'SUBMISSIONFAILED', # error occurred during submission phase
        ))


from aida.common.extendeddicts import DefaultFieldsAttributeDict

class CalcInfo(DefaultFieldsAttributeDict):
    """
    This object will store the data returned by the code plugin and to be
    passed to the ExecManager 
    
    # TODO:
    * retrieve_output_list
    * dynresources_info
    """
    _default_fields = (
        'jobEnvironment', # TODO UNDERSTAND THIS!
        'email',
        'emailOnStarted',
        'emailOnTerminated',
        'uuid',
        'prependText', # (both from computer and code)
        'appendText',  # (both from computer and code)
        'cmdlineParams',         # (including everything, also mpirun etc.; argv[0] is
                        #   the executable
        'stdinName',
        'stdoutName',
        'stderrName',
        'joinFiles',
        'queueName', 
        'numNodes',
        'numCpusPerNode',
        'priority',
        'maxWallclockSeconds',
        'maxMemoryKb',
        'rerunnable',
        )



#TODO Improve/implement this!
#class DynResourcesInfo(AttributeDict):
#    """
#    This object will contain a list of 'dynamical' resources to be 
#    passed from the code plugin to the ExecManager, containing
#    things like
#    * resources in the permanent repository, that will be simply
#      linked locally (but copied remotely on the remote computer)
#      to avoid a waste of permanent repository space
#    * remote resources to be directly copied over only remotely
#    """
#    pass

