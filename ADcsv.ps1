<#
.SYNOPSIS
	Adds or removes users from Active Directory given a CSV file
.DESCRIPTION
	The script parses a CSV file and stores commands to add or removes users from Active Directory. Before staging changes, and interactive prompt allows for modifications before staging changes.
.PARAMETER Path
	The path to the CSV file
.PARAMETER Action
	Possible actions: "Add", "Remove"
.PARAMETER Domain
	The domain to modify for example : domain.local
.PARAMETER headerString
	Defines a custom set of column names. Format must be a single string with column names separated by commas. For example "Column1, Column2" or "Column1,Column2". The default headerString can be modified in the script
.PARAMETER SafeMode
	If the flag SafeMode is present, instead of running the staging commands, it prints the commands to the terminal
.EXAMPLE
	.\ADcsv.ps1 -Path Users.csv -Action Add
#>
[CmdletBinding()]
param (
	[Parameter(Mandatory=$true)]
	[string]$Path,

	[Parameter(Mandatory=$true)]
	[ValidateSet("Add", "Remove")]
	[string]$Action,

	[Parameter(Mandatory=$true)]
	[string]$Domain,

	[switch]$SafeMode,

	#Modify this string to set a new default headerString value
	[string]$headerString = "First name, Last name, Department, Title, Location, Manager"
)


#Turning $headerString into an array then stripping all white space and \n 
#This means "column1, column2" and "column1,columns2" give the same array
$tempArray = $headerString -split ","
$columnArray = foreach ($str in $tempArray) {
	$str.Trim()
} 


$data = Import-Csv -Path $Path -Header $columnArray

$firstNameArray = @()
$lastNameArray = @()
$accountNameArray = @()

#Collecting First names, last names, and creating account names and storing them in their own arrays
#At the same time, it prints the Full name, Account name, and UPN of each user before staging the changes
$count = 0
foreach ($row in $data) {
	$count += 1

	$firstName = "$($row.$($columnArray[0]))"
	$lastName = "$($row.$($columnArray[1]))"

	#For example Jack Smith turns into j.smith
	$accountName = "$($firstName[0]).$lastName"


	$firstNameArray += $firstName
	$lastNameArray += $lastName
	$accountNameArray += $accountName

	Write-Output "User $count"
	Write-Output "Full name :           $firstName $lastName"
	Write-Output "Account Name :        $accountName"
	Write-Output "User Principal Name : $accountName@$Domain"
	Write-Output ""

}


#Shows the user the changes to be staged and stays in the loop until the user enters "y" or "n"
while ($true) {
	if ($Action.ToLower() -eq "add") {
		Write-Host "ADDING $count NEW USERS TO ACTIVE DIRECTORY" -ForegroundColor Green
	} else {
		Write-Host "REMOVING $count USERS FROM ACTIVE DIRECTORY" -ForegroundColor Red
	}
	Write-Output "These are the changes to be staged"
	$answer = Read-Host -Prompt "Stage Changes? [y/n]"
	if ($answer.ToLower() -eq "y") {
		break
	} elseif ($answer.ToLower() -eq "n") {
		exit 0
	}
}


#Iterates through the first name, last name, and account name arrays then builds a commandString which is either printed to the terminal or ran with "powershell $commandString"
for ($i = 0; $i -lt $count; $i++) {
	$firstName = $firstNameArray[$i]
	$lastName = $lastNameArray[$i]
	$accountName = $accountNameArray[$i]

	$commandString = "New-ADUser -Name ""$firstName $lastName"" -GivenName ""$firstName"" -Surname ""$lastName"" -SamAccountName ""$accountName"" -UserPrincipalName ""$accountName@$Domain"""


	if ($SafeMode) {
		Write-Output $commandString
		Write-Output ""
	} elseif ($Action.ToLower() -eq "add") {
		Invoke-Expression $commandString
	} else {
		Remove-ADUser -Identity $accountName
	}

}




