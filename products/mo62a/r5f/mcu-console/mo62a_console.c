/*
 * Mo62A MCU R5F console: answers short text commands from Linux over RPMsg.
 *
 * Added to the TI MCU+ SDK example ipc_rpmsg_echo_linux (BSD-3-Clause);
 * call mo62a_console_start() after RPMessage_waitForLinuxReady().
 */
#include <stdio.h>
#include <string.h>
#include <inttypes.h>
#include <kernel/dpl/ClockP.h>
#include <kernel/dpl/DebugP.h>
#include <kernel/dpl/TaskP.h>
#include <drivers/ipc_rpmsg.h>
#include <drivers/soc.h>
#include "../ipc_fw_version.h"
#include "FreeRTOS.h"
#include "task.h"

#define CONSOLE_ENDPT     (15U)
#define CONSOLE_SERVICE   "rpmsg_chrdev"   /* channel name the Linux rpmsg_char driver binds to */
#define CONSOLE_MAX_MSG   (496U)           /* 512-byte Linux buffer minus RPMsg header */
#define CONSOLE_TASK_PRI  (8U)
#define MAX_TASKS         (16U)

extern volatile uint8_t gbShutdown;        /* set by the TI example when Linux stops the core */

static uint8_t gConsoleStack[8*1024U] __attribute__((aligned(32)));
static TaskP_Object gConsoleTask;
static RPMessage_Object gConsoleObj;

static void cmd_tasks(char *out, size_t size)
{
    static const char *states[] = { "run", "ready", "block", "susp", "del", "inv" };
    TaskStatus_t task[MAX_TASKS];
    UBaseType_t n = uxTaskGetSystemState(task, MAX_TASKS, NULL);
    size_t len = snprintf(out, size, "%-20s %-5s %4s %10s\n", "task", "state", "prio", "stack_free");

    for (UBaseType_t i = 0; i < n && len < size; i++)
    {
        len += snprintf(out + len, size - len, "%-20.20s %-5s %4u %10u\n",
                        task[i].pcTaskName, states[task[i].eCurrentState],
                        (unsigned)task[i].uxCurrentPriority,
                        (unsigned)(task[i].usStackHighWaterMark * sizeof(StackType_t)));
    }
}

static void console_execute(char *line, char *out, size_t size)
{
    char *arg = strchr(line, ' ');

    if (arg != NULL)
    {
        *arg++ = '\0';
    }
    if (strcmp(line, "help") == 0)
    {
        snprintf(out, size, "commands: help version uptime load tasks echo <text>");
    }
    else if (strcmp(line, "version") == 0)
    {
        snprintf(out, size, "Mo62A MCU console, %s, built %s %s, %" PRIu64 " Hz",
                 IPC_FW_VERSION, __DATE__, __TIME__, SOC_getSelfCpuClk());
    }
    else if (strcmp(line, "uptime") == 0)
    {
        uint64_t ms = ClockP_getTimeUsec() / 1000U;
        snprintf(out, size, "%" PRIu64 ".%03u s", ms / 1000U, (unsigned)(ms % 1000U));
    }
    else if (strcmp(line, "load") == 0)
    {
        uint32_t load = TaskP_loadGetTotalCpuLoad();
        snprintf(out, size, "cpu load %u.%02u %%", (unsigned)(load / 100U), (unsigned)(load % 100U));
    }
    else if (strcmp(line, "tasks") == 0)
    {
        cmd_tasks(out, size);
    }
    else if (strcmp(line, "echo") == 0)
    {
        snprintf(out, size, "%s", arg != NULL ? arg : "");
    }
    else
    {
        snprintf(out, size, "unknown command '%s', try help", line);
    }
}

static void console_task_main(void *args)
{
    char line[CONSOLE_MAX_MSG + 1], reply[CONSOLE_MAX_MSG];
    uint16_t len, remoteCoreId;
    uint32_t remoteEndPt;

    DebugP_log("[MO62A CONSOLE] ready at end point %d\r\n", CONSOLE_ENDPT);
    while (gbShutdown == 0u)
    {
        len = CONSOLE_MAX_MSG;
        /* time out regularly so that a Linux stop request is noticed */
        if (RPMessage_recv(&gConsoleObj, line, &len, &remoteCoreId, &remoteEndPt,
                           ClockP_usecToTicks(100000U)) != SystemP_SUCCESS)
        {
            continue;
        }
        while (len > 0U && (line[len - 1U] == '\n' || line[len - 1U] == '\r'))
        {
            len--;
        }
        line[len] = '\0';
        console_execute(line, reply, sizeof(reply));
        RPMessage_send(reply, (uint16_t)strlen(reply), remoteCoreId, remoteEndPt,
                       CONSOLE_ENDPT, ClockP_usecToTicks(100000U));
    }
    RPMessage_destruct(&gConsoleObj);
    vTaskDelete(NULL);
}

void mo62a_console_start(void)
{
    RPMessage_CreateParams createParams;
    TaskP_Params params;
    int32_t status;

    RPMessage_CreateParams_init(&createParams);
    createParams.localEndPt = CONSOLE_ENDPT;
    status = RPMessage_construct(&gConsoleObj, &createParams);
    DebugP_assert(status == SystemP_SUCCESS);
    status = RPMessage_announce(CSL_CORE_ID_A53SS0_0, CONSOLE_ENDPT, CONSOLE_SERVICE);
    DebugP_assert(status == SystemP_SUCCESS);

    TaskP_Params_init(&params);
    params.name = "MO62A_CONSOLE";
    params.stackSize = sizeof(gConsoleStack);
    params.stack = gConsoleStack;
    params.priority = CONSOLE_TASK_PRI;
    params.taskMain = console_task_main;
    status = TaskP_construct(&gConsoleTask, &params);
    DebugP_assert(status == SystemP_SUCCESS);
}
