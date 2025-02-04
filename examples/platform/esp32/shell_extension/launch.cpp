/*
 *
 *    Copyright (c) 2021 Project CHIP Authors
 *
 *    Licensed under the Apache License, Version 2.0 (the "License");
 *    you may not use this file except in compliance with the License.
 *    You may obtain a copy of the License at
 *
 *        http://www.apache.org/licenses/LICENSE-2.0
 *
 *    Unless required by applicable law or agreed to in writing, software
 *    distributed under the License is distributed on an "AS IS" BASIS,
 *    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *    See the License for the specific language governing permissions and
 *    limitations under the License.
 */

#include "launch.h"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "heap_trace.h"
#include "sdkconfig.h"

#include <lib/shell/Engine.h>

namespace {

void MatterShellTask(void * args)
{
    chip::Shell::Engine::Root().RunMainLoop();
}

} // namespace

namespace chip {

void LaunchShell()
{
#if CONFIG_HEAP_TRACING_STANDALONE || CONFIG_HEAP_TASK_TRACKING
    idf::chip::RegisterHeapTraceCommands();
#endif // CONFIG_HEAP_TRACING_STANDALONE || CONFIG_HEAP_TASK_TRACKING
    xTaskCreate(&MatterShellTask, "chip_cli", 2048, NULL, 5, NULL);
}

} // namespace chip
