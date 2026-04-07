/**
 * Function to rotate an array to the right by a specified number of times.
 * @param {Array<any>} arr The array to rotate.
 * @param {number} k The number of times to rotate right.
 * @returns {Array<any>} The rotated array.
 */
function rotateArrayRight(arr, k) {
    const n = arr.length;
    if (n === 0) {
        return [];
    }

    // Calculate the effective rotation amount (k % n)
    // This handles cases where k is larger than the array length.
    const effectiveRotations = k % n;

    // If effectiveRotations is 0, no rotation is needed.
    if (effectiveRotations === 0) {
        return [...arr]; // Return a copy to maintain immutability principle
    }

    // A right rotation by 'k' means the last 'k' elements move to the front.
    // The new array is formed by: [last k elements] + [first n-k elements]
    const rotatedPart = arr.slice(n - effectiveRotations);
    const remainingPart = arr.slice(0, n - effectiveRotations);

    return [...rotatedPart, ...remainingPart];
}

// --- Execution for rotating exactly 2 times ---
const originalArray = [1, 2, 3, 4, 5];
const rotations = 2;

console.log("Original Array:", originalArray);

// We call the function specifically for 2 rotations as requested.
const rotatedArray = rotateArrayRight(originalArray, rotations);

console.log(`Array rotated ${rotations} times to the right.`);
console.log("Rotated Array:", rotatedArray);

// Example verification:
// [1, 2, 3, 4, 5] -> Rotate 1 -> [5, 1, 2, 3, 4]
// [5, 1, 2, 3, 4] -> Rotate 2 -> [4, 5, 1, 2, 3]
// The output should match this verification.