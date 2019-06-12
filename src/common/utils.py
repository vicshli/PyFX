from itertools import zip_longest
import xlrd


class SheetNotFoundException(BaseException):
    """Raised when an excel sheet does not exist."""
    pass


def check_if_sheet_exists(open_shee_func):
    """Decorator that raises `SheetNotFoundException` if the function fails.

    Raises:
        SheetNotFoundException
    """
    def wrapper(*args, **kwargs):
        try:
            return open_shee_func(*args, **kwargs)
        except:
            raise SheetNotFoundException
    return wrapper


@check_if_sheet_exists
def _open_sheet(workbook, index: int):
    """Open worksheet wrapper function.

    Args:
        workbook:   wb object returned by `xlrd.open_workbook()`
        index:      sheet number to be opened
    """
    return workbook.sheet_by_index(index)


def comp_xlsx(original_fname: str, new_fname: str, sheet_idx=0) -> bool:
    """Checks if 2 excel files are identical in content.

    By default, the function checks the first sheet. Override `sheet_idx` to 
    check a custom sheet.

    Return: `True` if the 2 sheets are the same, else `False`
    """

    is_the_same = True

    new = xlrd.open_workbook(new_fname)
    original = xlrd.open_workbook(original_fname)

    newsheet = _open_sheet(new, sheet_idx)
    oldsheet = _open_sheet(original, sheet_idx)

    for rownum in range(max(newsheet.nrows, oldsheet.nrows)):

        if rownum < newsheet.nrows:
            newrow = newsheet.row_values(rownum)
            oldrow = oldsheet.row_values(rownum)

            for colnum, (newcell, oldcell) in \
                    enumerate(zip_longest(newrow, oldrow)):
                if newcell != oldcell:
                    print("Row {} Col {} - {} != {}".format(
                        rownum + 1, colnum + 1, newcell, oldcell))
                    is_the_same = False
        else:
            print("Row {} missing".format(rownum + 1))
            is_the_same = False

    return is_the_same