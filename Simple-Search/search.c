#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <ctype.h> // Include this for tolower

// Function prototypes
void search_directory(const char *dir_path, const char *file_name, const char *file_type, int recursive, int case_insensitive);
int match_file(const char *file_name, const char *pattern, int case_insensitive);
void to_lowercase(char *str);

// Main function
int main(int argc, char *argv[]) {
    char dir_path[512];
    char file_name[256];
    char file_type[256];
    int recursive=0;
    int case_insensitive=0;

    // Collect search criteria from the user
    printf("Enter directory to search: ");
    fgets(dir_path, sizeof(dir_path), stdin);
    dir_path[strcspn(dir_path, "\n")]=0; // Remove newline character

    printf("Enter file name (or part of it): ");
    fgets(file_name, sizeof(file_name), stdin);
    file_name[strcspn(file_name, "\n")]=0;

    printf("Enter file type (e.g., .txt, .c), or leave blank: ");
    fgets(file_type, sizeof(file_type), stdin);
    file_type[strcspn(file_type, "\n")]=0;

    printf("Enable recursive search? (1 for yes, 0 for no): ");
    scanf("%d", &recursive);

    printf("Enable case-insensitive search? (1 for yes, 0 for no): ");
    scanf("%d", &case_insensitive);

    // Start the file search
    search_directory(dir_path, file_name, file_type, recursive, case_insensitive);

    return 0;
}

// Function to search a directory for matching files
void search_directory(const char *dir_path, const char *file_name, const char *file_type, int recursive, int case_insensitive) {
    struct dirent *entry;
    DIR *dp=opendir(dir_path);

    if (dp == NULL) {
        perror("opendir");
        return;
    }

    while ((entry=readdir(dp))) {
        if (strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0) {
            continue; // Skip current and parent directories
        }

        char full_path[512];
        snprintf(full_path, sizeof(full_path), "%s/%s", dir_path, entry->d_name);

        struct stat path_stat;
        stat(full_path, &path_stat);

        if (S_ISDIR(path_stat.st_mode)) {
            if (recursive) {
                // If recursive search is enabled, search subdirectories
                search_directory(full_path, file_name, file_type, recursive, case_insensitive);
            }
        } else {
            // Check if the file matches the search criteria
            if (match_file(entry->d_name, file_name, case_insensitive) &&
                (strlen(file_type) == 0 || strstr(entry->d_name, file_type))) {
                printf("Found file: %s\n", full_path);
            }
        }
    }

    closedir(dp);
}

// Function to check if a file name matches the pattern (with case sensitivity option)
int match_file(const char *file_name, const char *pattern, int case_insensitive) {
    char name_copy[256], pattern_copy[256];
    if (case_insensitive) {
        strcpy(name_copy, file_name);
        strcpy(pattern_copy, pattern);
        to_lowercase(name_copy);
        to_lowercase(pattern_copy);
        return strstr(name_copy, pattern_copy) != NULL;
    } else {
        return strstr(file_name, pattern) != NULL;
    }
}

// Function to convert a string to lowercase
void to_lowercase(char *str) {
    for (int i=0; str[i]; i++) {
        str[i]=tolower(str[i]);
    }
}

