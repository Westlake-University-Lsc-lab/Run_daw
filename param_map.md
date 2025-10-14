### DAW_Demo parameters list and meaning

| Parameter          | Value                                         | Meaning                                                                                    |
| ------------------ | --------------------------------------------- | ------------------------------------------------------------------------------------------ |
| `START_ACQ`        | SW                                            | Start acquisition signal source, software command starts the acquisition                   |
| FIRST_TRG          | First trigger signal source                   |
| LVDS               | LVDS output signal source                     |
| S_IN               | a level on the S_IN/GPI front panel connector |
| `SYNC_ENABLE`      | YES / NO                                      | Enable synchronization mode                                                                |
| `OUTFILE_RAW`      | YES                                           | Enable raw data output to file                                                             |
| `OUTFILE_PATH`     | /mnt/data/PMT/R8520_406                       | Output binary file path                                                                    |
| `OUTFILE_NAME`     | R8520_406_self_trigger                        | Output binary file name                                                                    |
| `OUTFILE_MAXSIZE`  | 1024                                          | Size of single output binary file in MB                                                    |
| `EXTERNAL_TRIGGER` | ACQUISITION_ONLY / DISABLED                   | Enable external trigger input                                                              |
| `GAIN_FACTOR`      | 0                                             | the input dynamic range (0->2Vpp, 1->0.5Vpp)                                               |
| `RECORD_LENGTH`    | 20                                            | MINIMUM record length, 10 samples each unit                                                |
| `MAX_TAIL`         | 0                                             | Maximum number of over-threshold samples, 4 samples each unit                              |
| `PRE_TRIGGER`      | 5                                             | the record length before the trigger, 4 samples each unit                                  |
| `N_LFW`            | 5                                             | samples collected after the over-threshold signal, 4 samples each unit                     |
| `BLINE_DEFMODE`    | YES / NO                                      | Use Default baseline value                                                                 |
| `BLINE_DEFVALUE`   | 8192                                          | default baseline value                                                                     |
| `PULSE_POLARITY`   | POSITIVE / NEGATIVE                           | signal polarity                                                                            |
| `SELF_TRIGGER`     | YES / NO                                      | Enable self-trigger mode                                                                   |
| `TRG_THRESHOLD`    | 20                                            | trigger threshold                                                                          |
| `ACQ_TIME`         | 300                                           | acquisition time in seconds                                                                |
| `DC_OFFSET`        | -40                                           | DC offset adjust, -50 range = -Vpp to 0, +50 range = 0 to +Vpp, 0 range = -Vpp/2 to +Vpp/2 |
| `ENABLE_INPUT`     | YES / NO                                      | enable/disable input signal                                                                |
|                    |                                               |                                                                                            |

## most useful parameters during configuring the DAW_Config.txt

`EXTERNAL_TRIGGER`, `SELF_TRIGGER`, `RECORD_LENGTH` ,
`TRG_THRESHOLD`, `OUTFILE_RAW`, `ACQ_TIME`
