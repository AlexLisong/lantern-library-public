# Code, content, and third-party notices

## Project code

The project's original software and technical documentation are licensed under
[MIT](../LICENSE). That grant does not automatically cover the creative book
content, trademarks, third-party fonts, models, or other separately owned material.

## Book content

The included stories, learning activities, illustrations, narration, PDFs, and
videos under `books/` and `archive/` are sample creative content. No separate
redistribution license has been granted for this content in this repository.
The MIT code license does not license these media. Ask the maintainers for
permission before redistributing or adapting them.

The illustration prompts and production notes identify AI-generated artwork.
Narration was generated with Kokoro-82M using the `af_heart` voice. Generated
content needs human editorial review; availability in this repository is not a
guarantee of exclusive rights, factual accuracy, or suitability for every learner.

Prompts and production sources are retained to explain the workflow. Archived
scripts describe the first edition and may require historical intermediate files;
the supported reusable workflow is under `scripts/`. Historical exporters use
explicit `LANTERN_LEGACY_WORKSPACE` and `LANTERN_LEGACY_SITE` environment variables
rather than the author's machine paths.

## Third-party components

- `web/assets/nunito.woff2`: Nunito, SIL Open Font License 1.1. The full font notice
  is preserved at [Nunito-LICENSE.txt](../web/assets/Nunito-LICENSE.txt).
- Kokoro-82M is an optional, separately downloaded model from
  [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M). Review its model
  and voice terms before generation. No model weights are distributed here.
- Python dependencies and system tools retain their own licenses. Consult the
  dependency distributions when packaging a runtime or derived product.

New content contributions must include authorship/source and explicit reuse
terms. Keep attribution with any distributed font or media bundle.
