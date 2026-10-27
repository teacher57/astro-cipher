# Examples

Each picture below was made with `astrocipher encode` and decodes back to the text next to it.
Try reading one with the [key sheet](../alphabet/key_sheet.jpg) before you look!

| Picture | Text | What the decoder reads | Seed |
|---|---|---|---|
| [hello_world.jpg](hello_world.jpg) | hello world | `HELLO WORLD` | 1 |
| [look_up_tonight.jpg](look_up_tonight.jpg) | look up tonight | `LOOK UP TONIGHT` | 2 |
| [the_stars_keep_our_secrets.jpg](the_stars_keep_our_secrets.jpg) | the stars keep our secrets | `THE STARS KEEP OUR SECRETS` | 3 |
| [meet_me_at_the_old_oak_at_9.jpg](meet_me_at_the_old_oak_at_9.jpg) | meet me at the old oak at 9 | `MEET ME AT THE OLD OAK AT 9` | 4 |
| [i_invented_a_cipher_in_2026.jpg](i_invented_a_cipher_in_2026.jpg) | i invented a cipher in 2026 | `I INVENTED A CIPHER IN 2026` | 5 |
| [orion_rises_at_10_pm.jpg](orion_rises_at_10_pm.jpg) | Orion rises at 10 PM, bring a blanket! | `ORION RISES AT 10 PM BRING A BLANKET` | 6 |

Punctuation counts as a space, so it disappears from the decoded text, and letters come back
in capitals. Rebuild them all with `python make_examples.py`; the seed makes each picture exactly
the same every time.
