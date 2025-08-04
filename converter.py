import numpy as np
import re
import os

def convert_mat_to_numpy(input_file='mat.txt', output_py_file='matrix_constants.py'):
    """
    Reads a text file containing MATLAB-style matrix definitions,
    converts them to NumPy arrays, prints their shapes, and saves them
    as NumPy array definitions in a Python file.
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: The file '{input_file}' was not found.")
        return

    # Remove comments and newlines to simplify parsing
    content = re.sub(r'%.*?\n', '', content)
    content = content.replace('\n', '').replace('\r', '')

    # Regex to find matrix assignments like Ex=[...];
    matrix_regex = re.compile(r'(\w+)s*=\s*\[(.*?)\];')

    matches = matrix_regex.finditer(content)

    print(f"Processing file: {input_file}")
    print("-" * 20)

    output_content = "import numpy as np\n\n"

    for match in matches:
        matrix_name = match.group(1)
        matrix_data_str = match.group(2)

        try:
            rows = matrix_data_str.strip().split(';')
            
            parsed_matrix = []
            for row_str in rows:
                row_str = row_str.strip()
                if not row_str:
                    continue
                # Split by comma or space, filter out empty strings
                numbers = [float(num) for num in re.split(r'[,|\s]+', row_str) if num]
                if numbers:
                    parsed_matrix.append(numbers)

            # Ensure the matrix is not empty and all rows have the same length
            if parsed_matrix and all(len(row) == len(parsed_matrix[0]) for row in parsed_matrix):
                matrix = np.array(parsed_matrix)
                
                print(f"Matrix '{matrix_name}' found.")
                print(f"Shape of '{matrix_name}': {matrix.shape}")

                # Format the array into a string for the Python file
                matrix_string = np.array2string(matrix, separator=', ', threshold=np.inf)
                output_content += f"{matrix_name} = np.array({matrix_string})\n\n"

            elif parsed_matrix:
                print(f"Matrix '{matrix_name}' has rows of different lengths. Skipping.")
                print("-" * 20)

        except Exception as e:
            print(f"Could not process matrix '{matrix_name}'. Error: {e}")

    try:
        with open(output_py_file, 'w', encoding='utf-8') as f:
            f.write(output_content)
        print(f"Successfully saved all matrices to '{output_py_file}'")
    except IOError as e:
        print(f"Error writing to file '{output_py_file}'. Error: {e}")


if __name__ == '__main__':
    convert_mat_to_numpy()