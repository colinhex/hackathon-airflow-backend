from datetime import datetime

from pydantic import BaseModel, Field
from typing_extensions import Optional, Dict

from unibas.common.environment.variables import ModelDumpVariables


class DateResult(BaseModel):
    date: Optional[datetime] = Field(None, description="Content Date.")

    def is_empty(self):
        return self.date is None

    def raise_if_empty(self) -> 'DateResult':
        if self.is_empty():
            raise ValueError('DateResult is empty.')
        return self

    def model_dump(self, **kwargs) -> Dict:
        """
        Dump the model data to a dictionary.

        Args:
            **kwargs: Additional keyword arguments for dumping the model.

        Returns:
            dict[str, Any]: The dumped model data.
        """
        stringify_datetime = kwargs.pop(ModelDumpVariables.STRINGIFY_DATETIME, True)
        dump = super().model_dump(**kwargs)
        if stringify_datetime and not self.is_empty():
            dump['date'] = dump['date'].isoformat()
        return dump

