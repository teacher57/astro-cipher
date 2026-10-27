# Examples

Each picture below was made with `astrocipher encode` and decodes back to the text next to it.
Try reading one with the [key sheet](../alphabet/key_sheet.jpg) before you look!

| Picture | Text | What the decoder reads | Seed |
|---|---|---|---|
| [hello_world.jpg](hello_world.jpg) | hello world | `HELLO WORLD` | 1 |
| [look_up_tonight.jpg](look_up_tonight.jpg) | look up tonight | `LOOK UP TONIGHT` | 2 |
| [the_stars_keep_our_secrets.jpg](the_stars_keep_our_secrets.jpg) | the stars keep our secrets | `THE STARS KEEP OUR SECRETS` | 3 |
| [meet_me_at_the_old_oak_at_dawn.jpg](meet_me_at_the_old_oak_at_dawn.jpg) | meet me at the old oak at dawn | `MEET ME AT THE OLD OAK AT DAWN` | 4 |
| [i_invented_a_cipher.jpg](i_invented_a_cipher.jpg) | i invented a cipher | `I INVENTED A CIPHER` | 5 |
| [orion_rises_late_tonight.jpg](orion_rises_late_tonight.jpg) | Orion rises late tonight, bring a blanket! | `ORION RISES LATE TONIGHT BRING A BLANKET` | 6 |

Punctuation counts as a space, so it disappears from the decoded text, and letters come back
in capitals. Rebuild them all with `python make_examples.py`; the seed makes each picture exactly
the same every time.
