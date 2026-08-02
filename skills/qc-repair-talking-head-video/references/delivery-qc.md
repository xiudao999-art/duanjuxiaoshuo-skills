# Final delivery QC

## Automatic checks

- Decode the entire file, not only `ffprobe` metadata.
- Verify video and audio streams, expected dimensions, constant frame rate, duration, and frame count.
- Measure integrated loudness, true peak, and loudness range against the project target.
- Detect black sequences and silence events.
- Verify the final spoken unit reaches the end without an unintended blank or frozen branded tail.

## Manual samples

Inspect:

1. cover/title;
2. one frame before and after every edit;
3. every repaired subtitle boundary;
4. every Frame or designed overlay at reveal and hold;
5. every CK replacement at onset and payoff;
6. the last caption and final frame.

Listen around every cut with headphones when possible. A valid container and correct frame count do not prove natural speech.

## Failure isolation

- Decode errors in the final only: rerender final output to a new path.
- Decode errors in the clean master: rebuild the master before packaging.
- Correct video but impossible loudness values: suspect corrupted audio packets and run a full decode.
- Subtitle mismatch only: rebuild subtitle and emphasis layers; do not re-encode source segments unnecessarily.
- Empty tail: shorten the timeline and all overlay/caption durations to the last complete spoken unit.

Never label a failed render as usable. Preserve failed reports for diagnosis and deliver only a passing file.
