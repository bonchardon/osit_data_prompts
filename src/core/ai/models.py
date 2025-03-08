from pydantic import Field, BaseModel


class IsCorruption(BaseModel):
    is_corruption_present: bool = Field(
        description=(
            '<|begin_of_text|> You will receive a text of news in Ukrainian language. '
            'You need to identify if a text of the news is about corruption or not. '
            'If the text is about corruption the response has to be True.'
            'If the text is not about corruption the response has to be False.'
            '<|end_of_text|> '
        ),
        default=False
    )


class Categories(BaseModel):
    categories: list[dict] = Field(
        description=(
            '<|begin_of_text> Withdraw following data from the text given:'
            '- сущности:'
            '- физическое лицо (может иметь должность в юридическом лице или государственном органе; '
            'может быть учредителем юридического лица или оффшора)'
            ' - юридическое лицо в Украине'
            ' - оффшор '
            ' - государственный орган'
            '<|end_of_text>'
        ),
        default=False
    )
