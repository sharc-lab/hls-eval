
// Copyright 2022 The XLS Authors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

const ARRAY_SIZE = u32:16;

fn prefix_sum(values: u16[ARRAY_SIZE]) -> u16[ARRAY_SIZE] {
    for (i, c): (u32, u16[ARRAY_SIZE]) in u32:0..u32:4 {
        let lookback = u32:1 << i;
        for (j, updated): (u32, u16[ARRAY_SIZE]) in u32:0..ARRAY_SIZE {
            if j < lookback { updated } else { update(updated, j, c[j] + c[j - lookback]) }
        }(c)
    }(values)
}
